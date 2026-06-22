from app.auth.jwt_handler import create_access_token


def auth_headers(role: str = "admin"):
    username = role
    token = create_access_token(username, role)
    return {"Authorization": f"Bearer {token}"}
