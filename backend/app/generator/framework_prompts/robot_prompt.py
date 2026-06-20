def build_robot_prompt(user_prompt: str, retrieved_context: str = "") -> str:
    return f"""
You are an expert Robot Framework automation engineer.

Generate a complete Robot Framework automation script for the user request.

USER REQUEST:
{user_prompt}

RELEVANT CONTEXT FROM EXISTING AUTOMATION REPOSITORY:
{retrieved_context}

INSTRUCTIONS:
- Use the retrieved context as the primary source of truth.
- Reuse existing libraries, variables, keyword names, API patterns, and validation style from the retrieved context.
- Do not invent APIs, endpoints, locators, libraries, or keywords if they are not present in the context.
- If the context contains RequestsLibrary examples, use RequestsLibrary style.
- If the context contains Browser or Playwright-style UI keywords, follow that style.
- If required information is missing, use clear placeholders instead of inventing values.

ROBOT FRAMEWORK RULES:
- Return only raw Robot Framework code.
- Do not use markdown or triple backticks.
- Include *** Settings ***.
- Include *** Variables *** when needed.
- Include *** Keywords *** when reusable steps are needed.
- Include *** Test Cases ***.
- Use [Arguments] inside keyword bodies.
- Do not define keyword arguments on the same line as the keyword name.
- Use correct Robot Framework spacing between arguments.
- Add verification/assertion steps.
- Generated code should pass robot --dryrun.

Generate only the Robot Framework code.
"""