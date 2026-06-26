import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from app.config import settings
from app.events.event_types import EventType

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        if not settings.kafka_enabled:
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8") if value else None,
        )
        await self._producer.start()

    async def stop(self):
        if self._producer:
            await self._producer.stop()

    async def publish(
        self,
        event_type: EventType,
        generation_id: str | None = None,
        user_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ):
        if not settings.kafka_enabled or not self._producer:
            return

        event = {
            "event_type": event_type.value,
            "generation_id": generation_id,
            "user_id": user_id,
            "payload": payload or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await self._producer.send_and_wait(
                settings.kafka_events_topic,
                key=generation_id or user_id or event_type.value,
                value=event,
            )
        except Exception:
            logger.exception("Kafka event publish failed")


kafka_events = KafkaEventProducer()