from fastapi.testclient import TestClient
import pytest
from app.main import app
from tests.auth_helper import auth_headers
client = TestClient(app)
pytestmark = pytest.mark.slow

def test_generate_robot_framework_code():
    client.post(
        "/api/v1/rag/ingest",
        headers=auth_headers(),
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    response = client.post(
        "/api/v1/generate",
        headers=auth_headers(),
        json={
            "user_prompt": "Create venue on Ruckus Cloud from login to verification",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["framework"] == "robot"
    assert "*** Test Cases ***" in data["generated_code"]


def test_generate_python_pytest_code():
    client.post(
        "/api/v1/rag/ingest",
        headers=auth_headers(),
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    response = client.post(
        "/api/v1/generate",
        headers=auth_headers(),
        json={
            "user_prompt": "Create venue on Ruckus Cloud using API",
            "framework": "python",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["framework"] == "python"
    assert "def test_" in data["generated_code"]


def test_generate_playwright_code():
    client.post(
        "/api/v1/rag/ingest",
        headers=auth_headers(),
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    response = client.post(

        "/api/v1/generate",
        headers=auth_headers(),
        json={
            "user_prompt": "Create venue on Ruckus Cloud using UI",
            "framework": "playwright",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["framework"] == "playwright"
    assert "@playwright/test" in data["generated_code"]