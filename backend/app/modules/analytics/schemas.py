"""Response schemas for organization analytics."""

from datetime import date

from pydantic import BaseModel


class OrganizationAnalyticsResponse(BaseModel):
    organization_id: str
    date_from: date
    date_to: date
    documents_uploaded: int
    documents_processed: int | None
    questions_asked: int | None
    reports_generated: int
    active_users: int
    processing_failures: int | None
    searches: int | None
    average_response_latency_ms: float | None
    ai_usage: int | None
    unavailable_metrics: list[str]


class OrganizationAnalyticsEnvelope(BaseModel):
    data: OrganizationAnalyticsResponse