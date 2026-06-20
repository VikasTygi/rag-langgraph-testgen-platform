from typing import List

from langchain_core.documents import Document


def build_python_prompt(
    user_prompt: str,
    retrieved_docs: List[Document],
    context: str,
) -> str:
    return f"""
You are a senior Python Pytest automation engineer.

User request:
{user_prompt}

Relevant historical Python automation code:
{context}

Generate a complete Python Pytest test script.

Python Pytest rules:
1. Return only raw Python code.
2. Do not use markdown.
3. Do not use triple backticks.
4. Use pytest-compatible test functions.
5. Use requests for API automation when task is API-based.
6. Use clear helper functions such as login_to_ruckus_cloud and create_venue.
7. Add assertions for status code and response body.
8. Use timeout in requests calls.
9. Do not hardcode secrets except placeholder demo values.
10. Code must be valid Python syntax and pass ast.parse().
11. Do not include explanations.

Generated Python code:
""".strip()