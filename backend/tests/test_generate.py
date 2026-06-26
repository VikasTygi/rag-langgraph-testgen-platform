from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_helper import auth_headers


client = TestClient(app)


@patch("app.routes.generate_routes.send_generation_job")
def test_generate_robot_code(mock_send_generation_job):
    mock_send_generation_job.return_value = {
        "MessageId": "test-message-id"
    }

    response = client.post(
        "/api/v1/generate",
        headers=auth_headers(),
        json={
            "user_prompt": "Create venue on Ruckus Cloud",
            "framework": "robot",
            "top_k": 3,
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "QUEUED"
    assert data["generation_id"].startswith("gen_")

    mock_send_generation_job.assert_not_called()