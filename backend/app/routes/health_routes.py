from fastapi import APIRouter

from app.config import get_settings
from app.models import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        app=settings.app_name,
    )