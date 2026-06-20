from typing import List

from langchain_core.documents import Document


def build_robot_prompt(
    user_prompt: str,
    retrieved_docs: List[Document],
    context: str,
) -> str:
    return f"""
You are a senior Robot Framework automation engineer.

User request:
{user_prompt}

Relevant historical Robot Framework / automation code:
{context}

Generate a complete Robot Framework test script.

Robot Framework rules:
1. Return only raw Robot Framework code.
2. Do not use markdown.
3. Do not use triple backticks.
4. Include *** Settings ***.
5. Include *** Variables *** when useful.
6. Include *** Keywords *** when reusable steps are useful.
7. Include *** Test Cases ***.
8. Prefer modern RequestsLibrary style:
   - Create Session
   - POST On Session
   - GET On Session
   - PUT On Session
   - DELETE On Session
9. Use Create Dictionary instead of Python Evaluate for simple payloads.
10. Pass variables between keywords using arguments or return values.
11. Do not use undefined variables.
12. Add validation using Should Be Equal, Should Be True, or Should Contain.
13. Generated code should pass robot --dryrun if required libraries are installed.

Generated Robot Framework code:
""".strip()