from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_repo():
    response = client.post(
        "/api/v1/ingest",
        json={
            "repo_path": "./sample_repos",
            "framework": "generic",
        },
    )

    assert response.status_code == 200
    assert response.json()["indexed_files"] >= 1
    assert response.json()["indexed_chunks"] >= 1