import asyncio
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.cache.rate_limiter import (
    check_active_job_limit,
    check_user_rate_limit,
    decrement_active_jobs,
    increment_active_jobs,
)
from app.cache.redis_client import set_json
from app.config import get_settings
from app.db.generation_store import (
    create_generation,
    update_generation_status,
)
from app.db.session import get_db
from app.events.event_types import EventType
from app.events.kafka_producer import kafka_events
from app.models import GenerateQueuedResponse, GenerateRequest
from app.queue.sqs_client import send_generation_job
from app.security.prompt_guard import validate_prompt


settings = get_settings()
router = APIRouter()


def limits_disabled() -> bool:
    return (
        settings.testing
        or os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true"
        or os.getenv("ENVIRONMENT", "").lower() == "test"
    )


@router.post(
    "/generate",
    response_model=GenerateQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_test_script(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("generate:test")),
):
    user_id = (
        current_user.get("sub")
        or current_user.get("username")
        or current_user.get("role")
        or "unknown"
    )

    safe_top_k = min(request.top_k, 5)

    if not limits_disabled():
        rate_allowed = await check_user_rate_limit(user_id)

        if not rate_allowed:
            await kafka_events.publish(
                EventType.USER_RATE_LIMITED,
                user_id=user_id,
                payload={
                    "framework": request.framework,
                    "reason": "rate_limit_exceeded",
                },
            )

            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
            )

        active_allowed = await check_active_job_limit(user_id)

        if not active_allowed:
            await kafka_events.publish(
                EventType.USER_RATE_LIMITED,
                user_id=user_id,
                payload={
                    "framework": request.framework,
                    "reason": "too_many_active_jobs",
                },
            )

            raise HTTPException(
                status_code=429,
                detail="Too many active jobs",
            )

    guard_result = validate_prompt(request.user_prompt)

    if not guard_result["allowed"]:
        await kafka_events.publish(
            EventType.PROMPT_BLOCKED,
            user_id=user_id,
            payload={
                "reason": guard_result.get("reason"),
                "category": guard_result.get("category"),
            },
        )

        raise HTTPException(
            status_code=403,
            detail=guard_result,
        )

    generation_id = f"gen_{uuid.uuid4().hex[:12]}"

    create_generation(
        db=db,
        generation_id=generation_id,
        user_id=user_id,
        framework=request.framework,
        prompt=request.user_prompt,
    )

    await set_json(
        key=f"generation_status:{generation_id}",
        value={
            "generation_id": generation_id,
            "status": "QUEUED",
        },
        ttl_seconds=settings.generation_status_ttl_seconds,
    )

    job = {
        "generation_id": generation_id,
        "user_id": user_id,
        "user_prompt": request.user_prompt,
        "framework": request.framework,
        "top_k": safe_top_k,
    }

    if settings.testing:
        await kafka_events.publish(
            EventType.GENERATION_REQUESTED,
            generation_id=generation_id,
            user_id=user_id,
            payload={
                "framework": request.framework,
                "top_k": safe_top_k,
                "testing": True,
            },
        )

        return {
            "generation_id": generation_id,
            "status": "QUEUED",
        }

    if not limits_disabled():
        await increment_active_jobs(user_id)

    try:
        await asyncio.to_thread(send_generation_job, job)

    except Exception as exc:
        if not limits_disabled():
            await decrement_active_jobs(user_id)

        update_generation_status(
            db=db,
            generation_id=generation_id,
            status="FAILED",
            error_message=f"Failed to queue generation job: {str(exc)}",
        )

        await set_json(
            key=f"generation_status:{generation_id}",
            value={
                "generation_id": generation_id,
                "status": "FAILED",
                "error_message": f"Failed to queue generation job: {str(exc)}",
            },
            ttl_seconds=settings.generation_status_ttl_seconds,
        )

        await kafka_events.publish(
            EventType.GENERATION_FAILED,
            generation_id=generation_id,
            user_id=user_id,
            payload={
                "reason": "sqs_queue_failed",
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to queue generation job",
        )

    await kafka_events.publish(
        EventType.GENERATION_REQUESTED,
        generation_id=generation_id,
        user_id=user_id,
        payload={
            "framework": request.framework,
            "top_k": safe_top_k,
        },
    )

    return {
        "generation_id": generation_id,
        "status": "QUEUED",
    }