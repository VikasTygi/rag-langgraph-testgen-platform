from app.config import get_settings
from app.generator.prompts import build_generation_prompt
from app.graph.state import TestGenerationState
from app.llm.ollama_llm import OllamaLLM
from app.rag.langchain_rag import LangChainRAGService
from app.validator.script_validator import ScriptValidator
from app.security.context_guard import control_rag_context
# from app.rag.vector_store import LangChainRAGService

settings = get_settings()


def clean_generated_code(code: str, framework: str | None = None) -> str:
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

    # Remove common unwanted first-line labels from LLM output
    unwanted_first_lines = {
        "framework",
        "robot",
        "robotframework",
        "python",
        "pytest",
        "typescript",
        "playwright",
    }

    lines = code.splitlines()

    while lines and lines[0].strip().lower() in unwanted_first_lines:
        lines.pop(0)

    code = "\n".join(lines).strip()

    # For Robot Framework, force output to start from first Robot section
    if framework and framework.lower() in ["robot", "robotframework"]:
        robot_start = code.find("*** Settings ***")
        if robot_start != -1:
            code = code[robot_start:].strip()

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


def retriever_node(state: dict) -> dict:
    user_prompt = state.get("user_prompt")
    framework = state.get("framework", "generic")
    top_k = state.get("top_k", 5)
    current_user = state.get("user")

    print("===== GENERATE RETRIEVER DEBUG =====")
    print("user_prompt:", user_prompt)
    print("framework:", framework)
    print("top_k:", top_k)
    print("user:", current_user)

    rag_service = LangChainRAGService()

    retrieved_docs = rag_service.search(
        query=user_prompt,
        framework=framework,
        top_k=top_k,
)

    print("retrieved_docs_count:", len(retrieved_docs))

    for index, doc in enumerate(retrieved_docs):
        print(f"doc {index + 1} metadata:", doc.metadata)
        print(f"doc {index + 1} content:", doc.page_content[:300])

    return {
        **state,
        "retrieved_docs": retrieved_docs,
        "retrieved_context_count": len(retrieved_docs),
    }

def generator_node(state: TestGenerationState) -> dict:
    retrieved_docs = state.get("retrieved_docs", [])

    if not retrieved_docs:
        return {
            "status": "need_more_context",
            "message": "No relevant automation context found.",
            "missing": [
                "login flow",
                "venue creation keyword",
                "verification logic",
            ],
            "generated_code": None,
            "valid": False,
            "errors": [],
            "validation_summary": "Generation skipped because no relevant automation context was found.",
        }

    llm = OllamaLLM()

    prompt = build_generation_prompt(
        user_prompt=state["user_prompt"],
        framework=state["framework"],
        retrieved_docs=retrieved_docs,
    )

    generated_code = clean_generated_code(
        llm.generate(prompt),
        framework=state["framework"],
    )

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
        "validation_result": result,
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

    fixed_code = clean_generated_code(
        llm.generate(fix_prompt),
        framework=state["framework"],
    )

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


def should_fix_or_finish(state: TestGenerationState) -> str:
    if state["valid"]:
        return "final_output"

    if state["fix_attempts"] < settings.max_fix_attempts:
        return "fixer"

    return "final_output"

def controlled_context_node(state: TestGenerationState) -> TestGenerationState:
    retrieved_docs = state.get("retrieved_docs", [])
    user_prompt = state["user_prompt"]
    framework = state["framework"]
    user = state.get("user", {})

    print("\n===== CONTROLLED CONTEXT DEBUG =====")
    print("docs before context guard:", len(retrieved_docs))
    print("user_prompt:", user_prompt)
    print("framework:", framework)
    print("user:", user)

    for index, doc in enumerate(retrieved_docs):
        print(f"\n--- context doc {index + 1} ---")
        print("type:", type(doc))

        if hasattr(doc, "metadata"):
            print("metadata:", doc.metadata)

        if hasattr(doc, "page_content"):
            print("content:", doc.page_content[:500])
        else:
            print("raw:", str(doc)[:500])

    context_result = control_rag_context(
        docs=retrieved_docs,
        user_prompt=user_prompt,
        framework=framework,
        user=user,
    )

    print("context_result:", context_result)

    if not context_result["allowed"]:
        state["status"] = "need_more_context"
        state["message"] = context_result["message"]
        state["missing"] = context_result["missing"]
        state["retrieved_docs"] = []
        state["retrieved_context_count"] = 0
        state["generated_code"] = None
        state["valid"] = False
        state["errors"] = []
        state["validation_summary"] = "Generation skipped because no controlled RAG context was found."
        state["stop_generation"] = True
        return state

    safe_docs = context_result["safe_docs"]

    state["status"] = "context_ready"
    state["message"] = "Controlled RAG context is available."
    state["missing"] = []
    state["retrieved_docs"] = safe_docs
    state["retrieved_context_count"] = len(safe_docs)
    state["stop_generation"] = False

    return state

def should_generate_or_stop(state: TestGenerationState) -> str:
    if state.get("stop_generation"):
        return "final_output"

    return "generator"

def final_output_node(state: TestGenerationState) -> TestGenerationState:
    if state.get("status") == "need_more_context":
        state["generated_code"] = None
        state["valid"] = False
        state["errors"] = []
        state["validation_summary"] = "Generation skipped because no relevant automation context was found."
        state["validation_result"] = {
            "valid": False,
            "errors": [],
            "validation_summary": state["validation_summary"],
        }
        return state

    if state.get("valid") is True:
        state["status"] = "success"

        if not state.get("message"):
            state["message"] = "Code generated and validated successfully."

    else:
        state["status"] = "validation_failed"

        if not state.get("message"):
            state["message"] = "Code was generated but validation failed."

    if not state.get("validation_result"):
        state["validation_result"] = {
            "valid": state.get("valid", False),
            "errors": state.get("errors", []),
            "validation_summary": state.get("validation_summary", ""),
        }

    return state