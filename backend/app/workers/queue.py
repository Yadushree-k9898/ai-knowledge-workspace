"""Redis connection helper for enqueuing ARQ jobs."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings


async def create_queue_pool() -> ArqRedis:
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))