from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Generation


TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "BLOCKED", "CONTEXT_NOT_FOUND"}


def create_generation(
    db: Session,
    generation_id: str,
    user_id: str,
    framework: str,
    prompt: str,
):
    generation = Generation(
        generation_id=generation_id,
        user_id=user_id,
        framework=framework,
        prompt=prompt,
        status="QUEUED",
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)
    return generation


def get_generation(db: Session, generation_id: str):
    return (
        db.query(Generation)
        .filter(Generation.generation_id == generation_id)
        .first()
    )


def update_generation_status(
    db: Session,
    generation_id: str,
    status: str,
    result_text: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
):
    generation = get_generation(db, generation_id)

    if not generation:
        return None

    generation.status = status
    generation.result_text = result_text
    generation.result_url = result_url
    generation.error_message = error_message
    generation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(generation)
    return generation


def is_terminal_status(db: Session, generation_id: str) -> bool:
    generation = get_generation(db, generation_id)
    return bool(generation and generation.status in TERMINAL_STATUSES)