import json
import logging

from app.cache.rate_limiter import decrement_active_jobs
from app.cache.redis_client import set_json
from app.config import settings
from app.db.generation_store import (
    is_terminal_status,
    update_generation_status,
)
from app.db.session import SessionLocal, init_db
from app.events.event_types import EventType
from app.events.kafka_producer import KafkaEventProducer
from app.graph.workflow import TestGenerationWorkflow
from app.queue.sqs_client import (
    delete_generation_job,
    receive_generation_jobs,
)


logger = logging.getLogger(__name__)


async def update_cached_status(
    generation_id: str,
    status: str,
    result_text: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
):
    await set_json(
        key=f"generation_status:{generation_id}",
        value={
            "generation_id": generation_id,
            "status": status,
            "result_url": result_url,
            "result_text": result_text,
            "error_message": error_message,
        },
        ttl_seconds=settings.generation_status_ttl_seconds,
    )


async def process_job(job: dict, kafka_events: KafkaEventProducer):
    generation_id = job["generation_id"]
    user_id = job["user_id"]

    db = SessionLocal()

    try:
        if is_terminal_status(db, generation_id):
            logger.info("Generation already processed: %s", generation_id)
            return

        update_generation_status(db, generation_id, "RUNNING")
        await update_cached_status(generation_id, "RUNNING")

        await kafka_events.publish(
            EventType.GENERATION_STARTED,
            generation_id=generation_id,
            user_id=user_id,
            payload={"framework": job["framework"]},
        )

        workflow = TestGenerationWorkflow()

        result = workflow.run(
            user_prompt=job["user_prompt"],
            framework=job["framework"],
            top_k=job["top_k"],
            user={"sub": user_id},
        )

        final_code = result.get("code") or result.get("final_code") or str(result)

        update_generation_status(
            db=db,
            generation_id=generation_id,
            status="SUCCEEDED",
            result_text=final_code,
            result_url=None,
        )

        await update_cached_status(
            generation_id=generation_id,
            status="SUCCEEDED",
            result_text=final_code,
            result_url=None,
        )

        await kafka_events.publish(
            EventType.GENERATION_SUCCEEDED,
            generation_id=generation_id,
            user_id=user_id,
            payload={"framework": job["framework"]},
        )

    except Exception as exc:
        logger.exception("Generation failed: %s", generation_id)

        update_generation_status(
            db=db,
            generation_id=generation_id,
            status="FAILED",
            error_message=str(exc),
        )

        await update_cached_status(
            generation_id=generation_id,
            status="FAILED",
            error_message=str(exc),
        )

        await kafka_events.publish(
            EventType.GENERATION_FAILED,
            generation_id=generation_id,
            user_id=user_id,
            payload={"error": str(exc)},
        )

        raise

    finally:
        await decrement_active_jobs(user_id)
        db.close()


async def consume_forever():
    init_db()

    kafka_events = KafkaEventProducer()
    await kafka_events.start()

    try:
        while True:
            messages = receive_generation_jobs(max_messages=5)

            if not messages:
                continue

            for message in messages:
                receipt_handle = message["ReceiptHandle"]

                try:
                    job = json.loads(message["Body"])
                    await process_job(job, kafka_events)

                    delete_generation_job(receipt_handle)

                except Exception:
                    logger.exception("Worker failed to process SQS message")
                    # Do not delete message.
                    # SQS will retry after visibility timeout.
                    # DLQ should catch poison messages later.

    finally:
        await kafka_events.stop()