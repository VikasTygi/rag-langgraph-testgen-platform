import ast
import subprocess
import tempfile
from pathlib import Path
from typing import List


class ScriptValidator:
    def validate(self, framework: str, code: str) -> dict:
        framework = framework.lower().strip()

        if framework in ["python", "pytest"]:
            return self._validate_python(code)

        if framework in ["robot", "robotframework"]:
            return self._validate_robot(code)

        if framework in ["playwright", "typescript", "ts"]:
            return self._validate_playwright(code)

        return {
            "valid": False,
            "errors": [f"Unsupported framework: {framework}"],
            "validation_summary": f"Unsupported framework: {framework}",
        }

    def _validate_python(self, code: str) -> dict:
        errors: List[str] = []

        try:
            ast.parse(code)
        except SyntaxError as exc:
            errors.append(f"Python syntax error: {exc}")

        if "def test_" not in code:
            errors.append("Pytest code must contain at least one test function starting with test_.")

        if "assert " not in code:
            errors.append("Pytest code must contain at least one assert statement.")

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "validation_summary": "Python validation passed." if valid else "Python validation failed.",
        }

    def _validate_robot(self, code: str) -> dict:
        errors: List[str] = []

        if "*** Settings ***" not in code:
            errors.append("Missing Robot Framework section: *** Settings ***")

        if "*** Test Cases ***" not in code:
            errors.append("Missing Robot Framework section: *** Test Cases ***")

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "generated.robot"
            file_path.write_text(code, encoding="utf-8")

            try:
                result = subprocess.run(
                    ["robot", "--dryrun", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    robot_error = result.stderr.strip() or result.stdout.strip()
                    errors.append(robot_error)

            except FileNotFoundError:
                errors.append("robot command not found. Install robotframework.")
            except Exception as exc:
                errors.append(f"Robot validation failed: {exc}")

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "validation_summary": "Robot dry-run validation passed." if valid else "Robot dry-run validation failed.",
        }

    def _validate_playwright(self, code: str) -> dict:
        errors: List[str] = []

        if "@playwright/test" not in code:
            errors.append("Missing import from '@playwright/test'.")

        if "test(" not in code and "test.describe" not in code:
            errors.append("Missing Playwright test() or test.describe() block.")

        if "async" not in code:
            errors.append("Playwright test should use async function.")

        if "expect(" not in code:
            errors.append("Playwright test should contain at least one expect assertion.")

        if "page.goto" not in code:
            errors.append("Playwright test should navigate using page.goto().")

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "validation_summary": "Playwright structure validation passed." if valid else "Playwright structure validation failed.",
        }