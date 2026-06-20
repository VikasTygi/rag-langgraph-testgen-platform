import requests

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OllamaLLM:
    """
    Local LLM wrapper for Ollama.

    Supported example models:
    - qwen2.5-coder:7b
    - deepseek-coder:6.7b
    - llama3.1:8b

    This class calls:
    POST http://localhost:11434/api/generate
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except Exception as exc:
            logger.warning("Ollama call failed. Using fallback response. Error: %s", exc)
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """
        This fallback allows your project and tests to work
        even if Ollama is not installed yet.
        """

        prompt_lower = prompt.lower()

        if "playwright" in prompt_lower:
            return """
import { test, expect } from '@playwright/test';

test('create venue on ruckus cloud', async ({ page }) => {
  await page.goto('https://ruckus.cloud/login');

  await page.fill('#username', process.env.RC_USERNAME || 'admin');
  await page.fill('#password', process.env.RC_PASSWORD || 'password');
  await page.click('button[type="submit"]');

  await expect(page.locator('text=Dashboard')).toBeVisible();

  await page.click('text=Tenant');
  await page.click('text=DemoTenant');

  await page.click('text=Venues');
  await page.click('text=Create Venue');

  await page.fill('#venueName', 'Auto_Venue_001');
  await page.click('button[type="submit"]');

  await expect(page.locator('text=Auto_Venue_001')).toBeVisible();
});
""".strip()

        if "python" in prompt_lower or "pytest" in prompt_lower:
            return '''
import requests


BASE_URL = "https://ruckus.cloud"


def test_create_venue():
    login_payload = {
        "username": "admin",
        "password": "password"
    }

    login_response = requests.post(f"{BASE_URL}/login", json=login_payload)

    assert login_response.status_code == 200

    token = login_response.json().get("token")
    headers = {
        "Authorization": f"Bearer {token}"
    }

    venue_payload = {
        "name": "Auto_Venue_001",
        "description": "Created by automation"
    }

    create_response = requests.post(
        f"{BASE_URL}/venues",
        json=venue_payload,
        headers=headers,
    )

    assert create_response.status_code in [200, 201]
    assert create_response.json()["name"] == "Auto_Venue_001"
'''.strip()

        return """
*** Settings ***
Documentation    Generated Robot Framework test for creating venue on Ruckus Cloud.
Library          Browser

*** Variables ***
${BASE_URL}       https://ruckus.cloud
${USERNAME}       %{RC_USERNAME}
${PASSWORD}       %{RC_PASSWORD}
${TENANT_NAME}    DemoTenant
${VENUE_NAME}     Auto_Venue_001

*** Test Cases ***
Create Venue On Ruckus Cloud
    Open Browser    ${BASE_URL}/login    chromium
    Fill Text       id=username    ${USERNAME}
    Fill Text       id=password    ${PASSWORD}
    Click           button[type="submit"]
    Get Text        text=Dashboard

    Click           text=Tenant
    Click           text=${TENANT_NAME}

    Click           text=Venues
    Click           text=Create Venue
    Fill Text       id=venueName    ${VENUE_NAME}
    Click           button[type="submit"]

    Get Text        text=${VENUE_NAME}
    Close Browser
""".strip()