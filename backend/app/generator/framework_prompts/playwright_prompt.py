def build_playwright_prompt(user_prompt: str, retrieved_context: str = "") -> str:
    return f"""
You are an expert Playwright TypeScript automation engineer.

Generate a complete Playwright TypeScript test for the following user request:

USER REQUEST:
{user_prompt}

RELEVANT CONTEXT FROM EXISTING AUTOMATION REPOSITORY:
{retrieved_context}

REQUIREMENTS:
- Use Playwright Test syntax.
- Use async/await.
- Use clear test steps.
- Add proper assertions.
- Use stable locators where possible.
- Do not add explanations outside the code.

Generate only the Playwright TypeScript code.
"""
