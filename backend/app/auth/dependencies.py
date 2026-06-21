from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import decode_access_token
from app.auth.rbac import has_permission


security = HTTPBearer(auto_error=False)

CI_API_KEY = "ci-secret-key-change-this"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_api_key: str | None = Header(default=None),
) -> dict:
    """
    Supports:
    1. JWT Bearer token for normal users
    2. X-API-Key for CI/CD systems
    """

    if x_api_key:
        if x_api_key != CI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        return {
            "username": "ci-system",
            "role": "ci-system",
            "auth_type": "api_key",
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    username = payload.get("sub")
    role = payload.get("role")

    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {
        "username": username,
        "role": role,
        "auth_type": "jwt",
    }


def require_permission(permission: str):
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user["role"]

        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' does not have permission '{permission}'",
            )

        return current_user

    return dependency