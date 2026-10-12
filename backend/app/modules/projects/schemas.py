"""
Pydantic schemas for the Projects module.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    """POST /organizations/{org_id}/projects"""
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Project name",
        examples=["Competitor Analysis"],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Project description",
        examples=["Research on competitors"],
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Project name must be at least 2 characters after trimming.")
        return stripped


class UpdateProjectRequest(BaseModel):
    """PATCH /projects/{project_id}"""
    name: str | None = Field(
        None,
        min_length=2,
        max_length=200,
        description="New project name",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="New description",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Project name must be at least 2 characters after trimming.")
        return stripped


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class ProjectResponse(BaseModel):
    """Single project data."""
    id: str
    organization_id: str
    name: str
    description: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummaryResponse(BaseModel):
    """Project summary with counts."""
    project_id: str
    name: str
    document_count: int = 0
    conversation_count: int = 0
    report_count: int = 0


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    page: int
    page_size: int
    total: int
