from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.cache.redis_client import get_json
from app.db.generation_store import get_generation
from app.db.session import get_db


router = APIRouter()


@router.get("/generations/{generation_id}")
async def get_generation_status(
    generation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("generate:test")),
):
    cached = await get_json(f"generation_status:{generation_id}")

    if cached:
        return cached

    generation = get_generation(db, generation_id)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    return {
        "generation_id": generation.generation_id,
        "status": generation.status,
        "result_url": generation.result_url,
        "result_text": generation.result_text,
        "error_message": generation.error_message,
    }