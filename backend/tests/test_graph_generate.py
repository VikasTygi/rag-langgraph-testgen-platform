from fastapi.testclient import TestClient
import pytest
from app.main import app
from tests.auth_helper import auth_headers
import shutil
from pathlib import Path

client = TestClient(app)
pytestmark = pytest.mark.slow

def test_langgraph_generate_robot_code():
    ingest_response = client.post(
        "/api/v1/rag/ingest",
        headers=auth_headers(),
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    assert ingest_response.status_code == 200, ingest_response.text

    response = client.post(
        "/api/v1/generate",
        headers=auth_headers(),
        json={
            "user_prompt": "Create venue on Ruckus Cloud from login to verification",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 202, response.text

    data = response.json()

    assert isinstance(data, dict)
    assert any(
        key in data for key in ["request_id", "job_id", "task_id", "generation_id", "id"]
    ), data