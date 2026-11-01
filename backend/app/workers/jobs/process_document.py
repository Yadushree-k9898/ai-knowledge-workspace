"""ARQ task for asynchronous document ingestion."""

import asyncio

from app.modules.documents.service import process_document_job


async def process_document(ctx: dict, job_id: int) -> None:
    """Run parsing and embedding outside the API process."""
    await asyncio.to_thread(process_document_job, job_id)
