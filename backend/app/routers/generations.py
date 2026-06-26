from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.artifact_store import S3ArtifactStore
from app.services.generation_history_service import get_generation, list_generations

router = APIRouter(prefix="/api/v1/generations", tags=["generations"])


@router.get("")
def get_generations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items = list_generations(db=db, limit=limit, offset=offset)

    return {
        "count": len(items),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(item.id),
                "framework": item.framework,
                "status": item.status,
                "created_by": item.created_by,
                "created_at": item.created_at,
                "output_s3_key": item.output_s3_key,
            }
            for item in items
        ],
    }


@router.get("/{generation_id}")
def get_generation_by_id(
    generation_id: UUID,
    db: Session = Depends(get_db),
):
    item = get_generation(db=db, generation_id=generation_id)

    if not item:
        raise HTTPException(status_code=404, detail="Generation not found")

    download_url = None
    if item.output_s3_key:
        download_url = S3ArtifactStore().presign_get_url(item.output_s3_key)

    return {
        "id": str(item.id),
        "user_prompt": item.user_prompt,
        "framework": item.framework,
        "generated_code": item.generated_code,
        "status": item.status,
        "created_by": item.created_by,
        "metadata": item.metadata_json,
        "output_s3_key": item.output_s3_key,
        "download_url": download_url,
        "created_at": item.created_at,
    }