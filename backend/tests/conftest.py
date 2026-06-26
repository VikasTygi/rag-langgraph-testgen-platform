import pytest
import os

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./rag_testgen_test.db"
os.environ["SQS_GENERATION_QUEUE_URL"] = "test-queue"
os.environ["KAFKA_ENABLED"] = "false"

import shutil
import pytest


@pytest.fixture(scope="session", autouse=True)
def clean_chroma_db_for_tests():
    shutil.rmtree("chroma_db", ignore_errors=True)
    yield
    shutil.rmtree("chroma_db", ignore_errors=True)

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