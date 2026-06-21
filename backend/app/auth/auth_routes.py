from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.jwt_handler import create_access_token


router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


FAKE_USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
    },
    "developer": {
        "password": "dev123",
        "role": "developer",
    },
    "viewer": {
        "password": "viewer123",
        "role": "viewer",
    },
}


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = FAKE_USERS_DB.get(request.username)

    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        username=request.username,
        role=user["role"],
    )

    return LoginResponse(
        access_token=token,
        role=user["role"],
    )