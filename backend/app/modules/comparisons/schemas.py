"""Request and response schemas for project document comparisons."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AttachProjectDocumentRequest(BaseModel):
    document_id: int = Field(..., gt=0)


class CreateComparisonRequest(BaseModel):
    document_ids: list[int] = Field(..., min_length=2, max_length=5)
    instructions: str | None = Field(None, max_length=5000)

    @field_validator("document_ids")
    @classmethod
    def validate_unique_documents(cls, document_ids: list[int]) -> list[int]:
        if len(set(document_ids)) != len(document_ids):
            raise ValueError("Choose each document only once.")
        return document_ids

    @field_validator("instructions")
    @classmethod
    def strip_instructions(cls, instructions: str | None) -> str | None:
        if instructions is None:
            return None
        return instructions.strip() or None


class ProjectDocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime | None
    added_at: datetime


class ComparisonResponse(BaseModel):
    id: str
    project_id: str
    document_ids: list[int]
    document_names: list[str]
    instructions: str | None
    status: str
    result: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime