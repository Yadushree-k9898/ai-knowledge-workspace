"""ARQ worker configuration."""

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.jobs.generate_comparison import generate_comparison
from app.workers.jobs.generate_report import generate_report
from app.workers.jobs.process_document import process_document


class WorkerSettings:
    functions = [generate_comparison, generate_report, process_document]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 2
    job_timeout = 600