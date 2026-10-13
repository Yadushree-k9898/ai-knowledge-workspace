"""Request and response schemas for asynchronous research reports."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ReportType(str, Enum):
    SUMMARY = "SUMMARY"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    RESEARCH_BRIEF = "RESEARCH_BRIEF"


class CreateReportRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    report_type: ReportType
    instructions: str | None = Field(None, max_length=5000)

    @field_validator("title")
    @classmethod
    def strip_title(cls, title: str) -> str:
        title = title.strip()
        if len(title) < 2:
            raise ValueError("Report title must be at least 2 characters after trimming.")
        return title

    @field_validator("instructions")
    @classmethod
    def strip_instructions(cls, instructions: str | None) -> str | None:
        if instructions is None:
            return None
        return instructions.strip() or None


class ReportResponse(BaseModel):
    id: str
    project_id: str
    created_by: str
    title: str
    report_type: ReportType
    instructions: str | None
    source_document_ids: list[int]
    status: str
    content: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime