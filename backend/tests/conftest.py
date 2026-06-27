import os
import shutil
from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).resolve().parent.parent / ".test_artifacts"
CHROMA_DIR = TEST_ROOT / "chroma_db"
HF_HOME = TEST_ROOT / "hf_home"
SENTENCE_TRANSFORMERS_HOME = TEST_ROOT / "sentence_transformers"


# Clean once before app/test modules create Chroma clients.
shutil.rmtree(TEST_ROOT, ignore_errors=True)
shutil.rmtree("chroma_db", ignore_errors=True)

TEST_ROOT.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
HF_HOME.mkdir(parents=True, exist_ok=True)
SENTENCE_TRANSFORMERS_HOME.mkdir(parents=True, exist_ok=True)


# Test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DISABLE_RATE_LIMIT"] = "true"

# Force vector DB to writable test folder
os.environ["CHROMA_DIR"] = str(CHROMA_DIR)
os.environ["CHROMA_PERSIST_DIR"] = str(CHROMA_DIR)
os.environ["VECTOR_STORE_DIR"] = str(CHROMA_DIR)

# Force HuggingFace cache to writable test folder
os.environ["HF_HOME"] = str(HF_HOME)
os.environ["TRANSFORMERS_CACHE"] = str(HF_HOME)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(SENTENCE_TRANSFORMERS_HOME)


@pytest.fixture(autouse=True)
def mock_ollama_llm(monkeypatch):
    def fake_generate(self, prompt: str):
        prompt_lower = prompt.lower()

        if "playwright" in prompt_lower:
            return """
import { test, expect } from '@playwright/test';

test('create venue on ruckus cloud', async ({ page }) => {
  await page.goto('https://ruckus.cloud/login');
  await page.fill('#username', 'admin');
  await page.fill('#password', 'password');
  await page.click('button[type="submit"]');
  await expect(page.locator('text=Dashboard')).toBeVisible();

  await page.click('text=Venues');
  await page.click('text=Create Venue');
  await page.fill('#venue-name', 'Auto_Venue_001');
  await page.click('button[type="submit"]');

  await expect(page.locator('text=Auto_Venue_001')).toBeVisible();
});
"""

        if "pytest" in prompt_lower or "python" in prompt_lower:
            return """
def test_create_venue_api():
    token = login_to_ruckus_cloud("admin", "password")
    venue = create_venue(token=token, venue_name="Auto_Venue_001")
    assert venue["name"] == "Auto_Venue_001"
"""

        return """
*** Settings ***
Library    RequestsLibrary

*** Variables ***
${BASE_URL}       https://ruckus.cloud
${USERNAME}       admin
${PASSWORD}       password
${VENUE_NAME}     Auto_Venue_001

*** Test Cases ***
Create Venue On Ruckus Cloud
    ${token}=    Login To Ruckus Cloud API
    ${venue}=    Create Venue API    ${token}
    Should Be Equal    ${venue["name"]}    ${VENUE_NAME}

*** Keywords ***
Login To Ruckus Cloud API
    Create Session    ruckus    ${BASE_URL}
    ${payload}=    Create Dictionary    username=${USERNAME}    password=${PASSWORD}
    ${response}=    POST On Session    ruckus    /login    json=${payload}
    Should Be Equal As Integers    ${response.status_code}    200
    ${token}=    Set Variable    ${response.json()["token"]}
    RETURN    ${token}

Create Venue API
    [Arguments]    ${token}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${payload}=    Create Dictionary    name=${VENUE_NAME}
    ${response}=    POST On Session    ruckus    /venues    headers=${headers}    json=${payload}
    Should Be Equal As Integers    ${response.status_code}    201
    RETURN    ${response.json()}
"""

    monkeypatch.setattr(
        "app.llm.ollama_llm.OllamaLLM.generate",
        fake_generate,
        raising=True,
    )