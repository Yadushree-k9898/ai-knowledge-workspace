"""ARQ worker configuration."""

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.jobs.generate_comparison import generate_comparison
from app.workers.jobs.generate_report import generate_report


class WorkerSettings:
    functions = [generate_comparison, generate_report]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 2
    job_timeout = 600