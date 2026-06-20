from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_repo():
    client.post(
        "/api/v1/ingest",
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    response = client.post(
        "/api/v1/search",
        json={
            "query": "create venue on ruckus cloud",
            "framework": "robot",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1