from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_robot_code():
    client.post(
        "/api/v1/ingest",
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "Create venue on Ruckus Cloud",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    assert "generated_code" in response.json()
    assert response.json()["retrieved_context_count"] >= 1