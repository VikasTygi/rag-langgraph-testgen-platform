def clean_generated_code(code: str, framework: str) -> str:
    if not code:
        return ""

    cleaned = code.strip()

    # Remove markdown code fences if LLM returns them
    cleaned = cleaned.replace("```robot", "")
    cleaned = cleaned.replace("```python", "")
    cleaned = cleaned.replace("```typescript", "")
    cleaned = cleaned.replace("```ts", "")
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()

    framework = framework.lower()

    # For Robot Framework, remove unwanted text before first Robot section
    if framework == "robot":
        robot_sections = [
            "*** Settings ***",
            "*** Variables ***",
            "*** Test Cases ***",
            "*** Keywords ***",
        ]

        start_indexes = [
            cleaned.find(section)
            for section in robot_sections
            if cleaned.find(section) != -1
        ]

        if start_indexes:
            cleaned = cleaned[min(start_indexes):]

    return cleaned.strip()
