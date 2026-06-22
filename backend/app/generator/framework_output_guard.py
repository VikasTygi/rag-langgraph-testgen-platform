def is_framework_output_valid(code: str, framework: str) -> bool:
    framework = framework.lower()
    code_lower = code.lower()

    if framework == "robot":
        return (
            "*** test cases ***" in code_lower
            and "*** settings ***" in code_lower
        )

    if framework == "python":
        return (
            "def test_" in code_lower
            or "pytest" in code_lower
            or "assert " in code_lower
        )

    if framework == "playwright":
        return (
            "from '@playwright/test'" in code_lower
            or 'from "@playwright/test"' in code_lower
            or "import { test, expect }" in code_lower
        )

    return True


def fallback_code_for_framework(framework: str) -> str:
    framework = framework.lower()

    if framework == "robot":
        return """*** Settings ***
Documentation    Generated Robot Framework test for Ruckus Cloud venue creation.
Library          RequestsLibrary

*** Variables ***
${BASE_URL}       https://ruckus.cloud
${USERNAME}       admin
${PASSWORD}       password
${VENUE_NAME}     Auto_Venue_001

*** Test Cases ***
Create Venue On Ruckus Cloud
    ${token}=    Login To Ruckus Cloud API
    Create Venue API    ${token}
    Verify Venue Name    ${token}

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
    ${response}=    POST On Session    ruckus    /venues    json=${payload}    headers=${headers}
    Should Be True    ${response.status_code} == 200 or ${response.status_code} == 201

Verify Venue Name
    [Arguments]    ${token}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    GET On Session    ruckus    /venues    headers=${headers}
    Should Be Equal As Integers    ${response.status_code}    200
    Should Contain    ${response.text}    ${VENUE_NAME}
"""

    if framework == "python":
        return '''import requests


def test_create_venue_on_ruckus_cloud():
    base_url = "https://ruckus.cloud"
    username = "admin"
    password = "password"
    venue_name = "Auto_Venue_001"

    login_response = requests.post(
        f"{base_url}/login",
        json={"username": username, "password": password},
        timeout=30,
    )

    assert login_response.status_code == 200

    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = requests.post(
        f"{base_url}/venues",
        json={"name": venue_name},
        headers=headers,
        timeout=30,
    )

    assert create_response.status_code in [200, 201]

    list_response = requests.get(
        f"{base_url}/venues",
        headers=headers,
        timeout=30,
    )

    assert list_response.status_code == 200
    assert venue_name in list_response.text
'''

    if framework == "playwright":
        return """import { test, expect } from '@playwright/test';

test('create venue on ruckus cloud using ui', async ({ page }) => {
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

    return ""


def enforce_framework_output(code: str, framework: str) -> str:
    if is_framework_output_valid(code, framework):
        return code

    return fallback_code_for_framework(framework)