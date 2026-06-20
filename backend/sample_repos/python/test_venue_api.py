import requests


BASE_URL = "https://ruckus.cloud"


def login_to_ruckus_cloud(username: str, password: str) -> str:
    payload = {
        "username": username,
        "password": password,
    }

    response = requests.post(f"{BASE_URL}/login", json=payload, timeout=30)

    assert response.status_code == 200

    return response.json()["token"]


def create_venue(token: str, venue_name: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "name": venue_name,
        "description": "Created from automation",
    }

    response = requests.post(
        f"{BASE_URL}/venues",
        json=payload,
        headers=headers,
        timeout=30,
    )

    assert response.status_code in [200, 201]

    return response.json()


def test_create_venue_api():
    token = login_to_ruckus_cloud("admin", "password")

    venue = create_venue(
        token=token,
        venue_name="Auto_Venue_001",
    )

    assert venue["name"] == "Auto_Venue_001"