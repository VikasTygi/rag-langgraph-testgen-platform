import json
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
    )



async def set_json(key: str, value: dict[str, Any], ttl_seconds: int | None = None):
    if settings.testing:
        _test_cache[key] = json.dumps(value)
        return

    data = json.dumps(value)

    if ttl_seconds:
        await redis_client.set(key, data, ex=ttl_seconds)
    else:
        await redis_client.set(key, data)


async def get_json(key: str) -> dict[str, Any] | None:
    if settings.testing:
        data = _test_cache.get(key)
        return json.loads(data) if data else None

    data = await redis_client.get(key)

    if not data:
        return None

    return json.loads(data)


async def delete_key(key: str):
    if settings.testing:
        _test_cache.pop(key, None)
        return

    await redis_client.delete(key)