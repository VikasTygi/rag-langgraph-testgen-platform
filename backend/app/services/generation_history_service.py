from sqlalchemy.orm import Session

from app.db.models import GenerationHistory


def create_generation_history(
    db: Session,
    user_prompt: str,
    framework: str,
    generated_code: str | None,
    output_s3_key: str | None,
    status: str,
    created_by: str | None = None,
    metadata_json: dict | None = None,
) -> GenerationHistory:
    item = GenerationHistory(
        user_prompt=user_prompt,
        framework=framework,
        generated_code=generated_code,
        output_s3_key=output_s3_key,
        status=status,
        created_by=created_by,
        metadata_json=metadata_json or {},
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def list_generations(db: Session, limit: int = 20, offset: int = 0):
    return (
        db.query(GenerationHistory)
        .order_by(GenerationHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_generation(db: Session, generation_id):
    return (
        db.query(GenerationHistory)
        .filter(GenerationHistory.id == generation_id)
        .first()
    )