from fastapi.testclient import TestClient
import pytest
from app.main import app
from tests.auth_helper import auth_headers
client = TestClient(app)
pytestmark = pytest.mark.slow

def test_generate_robot_code():
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
            "user_prompt": "Create venue on Ruckus Cloud",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    assert "generated_code" in response.json()
    assert response.json()["retrieved_context_count"] >= 1