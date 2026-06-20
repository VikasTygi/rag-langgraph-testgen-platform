from app.config import get_settings
from app.generator.prompts import build_generation_prompt
from app.graph.state import TestGenerationState
from app.llm.ollama_llm import OllamaLLM
from app.rag.langchain_rag import LangChainRAGService
from app.validator.script_validator import ScriptValidator

settings = get_settings()


def clean_generated_code(code: str) -> str:
    code = code.strip()

    prefixes = [
        "```robot",
        "```python",
        "```typescript",
        "```ts",
        "```javascript",
        "```",
    ]

    for prefix in prefixes:
        if code.startswith(prefix):
            code = code[len(prefix):].strip()

    if code.endswith("```"):
        code = code[:-3].strip()

    return code


def planner_node(state: TestGenerationState) -> dict:
    framework = state["framework"]
    user_prompt = state["user_prompt"]

    plan = f"""
Task: Generate validated {framework} automation code.

User request:
{user_prompt}

Validation-aware workflow:
1. Understand the required automation flow.
2. Retrieve similar historical automation code from ChromaDB.
3. Generate framework-specific code.
4. Validate generated code using {framework}-specific validation.
5. If validation fails, send validation errors and bad code to the fixer node.
6. Retry fix up to {settings.max_fix_attempts} time(s).
7. Return final code with validation result.
""".strip()

    return {
        "plan": plan,
    }


def retriever_node(state: TestGenerationState) -> dict:
    rag_service = LangChainRAGService()

    docs = rag_service.search(
        query=state["user_prompt"],
        framework=state["framework"],
        top_k=state["top_k"],
    )

    # fallback to generic search if framework-specific search returns nothing
    if not docs:
        docs = rag_service.search(
            query=state["user_prompt"],
            framework="generic",
            top_k=state["top_k"],
        )

    print(f"DEBUG: LangGraph retrieved_docs count = {len(docs)}")

    return {
        "retrieved_docs": docs,
    }

def generator_node(state: TestGenerationState) -> dict:
    llm = OllamaLLM()

    prompt = build_generation_prompt(
        user_prompt=state["user_prompt"],
        framework=state["framework"],
        retrieved_docs=state["retrieved_docs"],
    )

    generated_code = clean_generated_code(llm.generate(prompt))

    return {
        "generated_code": generated_code,
    }


def validator_node(state: TestGenerationState) -> dict:
    validator = ScriptValidator()

    result = validator.validate(
        framework=state["framework"],
        code=state["generated_code"],
    )

    return {
        "valid": result["valid"],
        "errors": result["errors"],
        "validation_summary": result["validation_summary"],
    }


def fixer_node(state: TestGenerationState) -> dict:
    llm = OllamaLLM()

    framework = state["framework"].lower()
    errors_text = "\n".join(state["errors"])

    framework_rules = get_framework_fix_rules(framework)

    fix_prompt = f"""
You are a senior automation framework expert.

The generated {state["framework"]} code failed validation.

Original user request:
{state["user_prompt"]}

Validation summary:
{state["validation_summary"]}

Validation errors:
{errors_text}

Invalid generated code:
{state["generated_code"]}

Fix the code using these framework-specific rules:
{framework_rules}

Output rules:
1. Return only corrected raw code.
2. Do not use markdown.
3. Do not use triple backticks.
4. Do not explain.
5. Keep the same framework: {state["framework"]}.
6. Fix only syntax, structure, undefined variables, missing imports, and framework compliance issues.
""".strip()

    fixed_code = clean_generated_code(llm.generate(fix_prompt))

    return {
        "generated_code": fixed_code,
        "fix_attempts": state["fix_attempts"] + 1,
    }


def get_framework_fix_rules(framework: str) -> str:
    if framework in ["robot", "robotframework"]:
        return """
Robot Framework:
- Must include *** Settings *** and *** Test Cases ***.
- Use correct Robot Framework table spacing.
- Use installed libraries only.
- Prefer RequestsLibrary with Create Session and POST On Session.
- Use Create Dictionary for payloads and headers.
- Pass token as an argument instead of using undefined variables.
- Every keyword step must be indented under a test case or keyword.
- Code must pass robot --dryrun.
""".strip()

    if framework in ["python", "pytest"]:
        return """
Python Pytest:
- Code must pass ast.parse().
- Must include at least one test function named test_*.
- Must include assert statements.
- Use requests with timeout for API calls.
- Avoid undefined variables.
- Keep imports valid.
""".strip()

    if framework in ["playwright", "typescript", "ts"]:
        return """
Playwright TypeScript:
- Must import test and expect from '@playwright/test'.
- Must contain a test() block.
- Test function must be async.
- Must use page.goto().
- Must include expect assertions.
- Avoid undefined variables.
""".strip()

    return "Fix syntax and framework compliance issues."


def final_output_node(state: TestGenerationState) -> dict:
    return {}


def should_fix_or_finish(state: TestGenerationState) -> str:
    if state["valid"]:
        return "final_output"

    if state["fix_attempts"] < settings.max_fix_attempts:
        return "fixer"

    return "final_output"