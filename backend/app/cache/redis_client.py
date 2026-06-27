import json
import os
from typing import Any

import redis.asyncio as redis

from app.config import get_settings


settings = get_settings()

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)

_test_cache: dict[str, str] = {}


def redis_disabled_for_tests() -> bool:
    return (
        settings.testing
        or os.getenv("ENVIRONMENT", "").lower() == "test"
        or os.getenv("DISABLE_REDIS", "false").lower() == "true"
        or os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true"
    )


async def set_json(key: str, value: dict[str, Any], ttl_seconds: int | None = None):
    data = json.dumps(value)

    if redis_disabled_for_tests():
        _test_cache[key] = data
        return None

    if ttl_seconds:
        await redis_client.set(key, data, ex=ttl_seconds)
    else:
        await redis_client.set(key, data)


async def get_json(key: str) -> dict[str, Any] | None:
    if redis_disabled_for_tests():
        data = _test_cache.get(key)
        return json.loads(data) if data else None

    data = await redis_client.get(key)

    if not data:
        return None

    return json.loads(data)


async def delete_key(key: str):
    if redis_disabled_for_tests():
        _test_cache.pop(key, None)
        return None

    await redis_client.delete(key)