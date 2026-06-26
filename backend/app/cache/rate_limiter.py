from app.cache.redis_client import redis_client
from app.config import get_settings


settings = get_settings()

_test_rate_counters: dict[str, int] = {}
_test_active_jobs: dict[str, int] = {}


async def check_user_rate_limit(user_id: str) -> bool:
    if settings.testing:
        key = f"rate_limit:generation:{user_id}"
        _test_rate_counters[key] = _test_rate_counters.get(key, 0) + 1
        return _test_rate_counters[key] <= settings.user_rate_limit_per_minute

    key = f"rate_limit:generation:{user_id}"

    current = await redis_client.incr(key)

    if current == 1:
        await redis_client.expire(key, 60)

    return current <= settings.user_rate_limit_per_minute


async def get_active_jobs(user_id: str) -> int:
    if settings.testing:
        return _test_active_jobs.get(user_id, 0)

    value = await redis_client.get(f"active_jobs:{user_id}")
    return int(value or 0)


async def increment_active_jobs(user_id: str):
    if settings.testing:
        _test_active_jobs[user_id] = _test_active_jobs.get(user_id, 0) + 1
        return _test_active_jobs[user_id]

    key = f"active_jobs:{user_id}"
    value = await redis_client.incr(key)
    await redis_client.expire(key, 3600)
    return value


async def decrement_active_jobs(user_id: str):
    if settings.testing:
        _test_active_jobs[user_id] = max(_test_active_jobs.get(user_id, 0) - 1, 0)
        return _test_active_jobs[user_id]

    key = f"active_jobs:{user_id}"
    value = await redis_client.decr(key)

    if value <= 0:
        await redis_client.delete(key)

    return max(value, 0)


async def check_active_job_limit(user_id: str) -> bool:
    active = await get_active_jobs(user_id)
    return active < settings.max_active_jobs_per_user