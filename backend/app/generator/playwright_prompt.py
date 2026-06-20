from typing import List

from langchain_core.documents import Document


def build_playwright_prompt(
    user_prompt: str,
    retrieved_docs: List[Document],
    context: str,
) -> str:
    return f"""
You are a senior Playwright TypeScript automation engineer.

User request:
{user_prompt}

Relevant historical Playwright automation code:
{context}

Generate a complete Playwright TypeScript test script.

Playwright TypeScript rules:
1. Return only raw TypeScript code.
2. Do not use markdown.
3. Do not use triple backticks.
4. Import test and expect from '@playwright/test'.
5. Use test('...', async ({{ page }}) => {{ ... }}).
6. Use page.goto, page.fill, page.click, and expect assertions.
7. Use stable locators where possible.
8. Use process.env for username/password placeholders.
9. Verify successful login before creating venue.
10. Verify venue creation at the end.
11. Code should contain at least one expect assertion.
12. Do not include explanations.

Generated Playwright TypeScript code:
""".strip()