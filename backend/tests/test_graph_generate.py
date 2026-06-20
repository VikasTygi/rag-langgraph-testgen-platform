from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_langgraph_generate_robot_code():
    ingest_response = client.post(
        "/api/v1/ingest",
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    assert ingest_response.status_code == 200

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "Create venue on Ruckus Cloud from login to verification",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["framework"] == "robot"
    assert data["user_prompt"] == "Create venue on Ruckus Cloud from login to verification"
    assert data["retrieved_context_count"] >= 1
    assert "generated_code" in data
    assert "valid" in data
    assert "errors" in data
    assert "fix_attempts" in data