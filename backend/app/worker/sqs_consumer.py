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


async def publish_kafka_event(
    kafka_events: KafkaEventProducer | None,
    event_type: EventType,
    generation_id: str,
    user_id: str,
    payload: dict,
):
    if not settings.kafka_enabled or kafka_events is None:
        logger.info("Kafka disabled. Skipping event publish: %s", event_type)
        return

    await kafka_events.publish(
        event_type,
        generation_id=generation_id,
        user_id=user_id,
        payload=payload,
    )


async def process_job(job: dict, kafka_events: KafkaEventProducer | None):
    generation_id = job["generation_id"]
    user_id = job["user_id"]

    db = SessionLocal()

    try:
        if is_terminal_status(db, generation_id):
            logger.info("Generation already processed: %s", generation_id)
            return

        update_generation_status(db, generation_id, "RUNNING")
        await update_cached_status(generation_id, "RUNNING")

        await publish_kafka_event(
            kafka_events=kafka_events,
            event_type=EventType.GENERATION_STARTED,
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

        await publish_kafka_event(
            kafka_events=kafka_events,
            event_type=EventType.GENERATION_SUCCEEDED,
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

        await publish_kafka_event(
            kafka_events=kafka_events,
            event_type=EventType.GENERATION_FAILED,
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

    kafka_events: KafkaEventProducer | None = None

    if settings.kafka_enabled:
        kafka_events = KafkaEventProducer()
        await kafka_events.start()
        logger.info("Kafka producer started.")
    else:
        logger.info("Kafka disabled. Worker will skip Kafka event publishing.")

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
        if kafka_events is not None:
            await kafka_events.stop()
            logger.info("Kafka producer stopped.")