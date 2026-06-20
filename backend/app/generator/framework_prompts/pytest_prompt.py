def build_pytest_prompt(user_prompt: str, retrieved_context: str = "") -> str:
    return f"""
You are an expert Python Pytest automation engineer.

Generate a complete Pytest automation script for the following user request:

USER REQUEST:
{user_prompt}

RELEVANT CONTEXT FROM EXISTING AUTOMATION REPOSITORY:
{retrieved_context}

REQUIREMENTS:
- Use Python Pytest syntax.
- Use clear function names.
- Add assertions.
- Use reusable helper functions where needed.
- Do not add explanations outside the code.

Generate only the Python code.
"""
