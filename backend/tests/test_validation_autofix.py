from app.validator.script_validator import ScriptValidator


def test_python_validation_fails_for_invalid_syntax():
    validator = ScriptValidator()

    code = """
def test_sample(
    assert 1 == 1
"""

    result = validator.validate("python", code)

    assert result["valid"] is False
    assert len(result["errors"]) >= 1


def test_python_validation_passes_for_valid_pytest():
    validator = ScriptValidator()

    code = """
def test_sample():
    assert 1 == 1
"""

    result = validator.validate("python", code)

    assert result["valid"] is True
    assert result["errors"] == []


def test_playwright_validation_fails_without_expect():
    validator = ScriptValidator()

    code = """
import { test } from '@playwright/test';

test('sample', async ({ page }) => {
  await page.goto('https://example.com');
});
"""

    result = validator.validate("playwright", code)

    assert result["valid"] is False
    assert "Playwright test should contain at least one expect assertion." in result["errors"]


def test_playwright_validation_passes():
    validator = ScriptValidator()

    code = """
import { test, expect } from '@playwright/test';

test('sample', async ({ page }) => {
  await page.goto('https://example.com');
  await expect(page.locator('body')).toBeVisible();
});
"""

    result = validator.validate("playwright", code)

    assert result["valid"] is True
    assert result["errors"] == []