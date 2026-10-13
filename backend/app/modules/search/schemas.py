from pydantic import BaseModel, Field, field_validator


class ProjectSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=10, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Search query cannot be empty.")
        return value


class ProjectSearchResult(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    text: str
    distance: float | None


class ProjectSearchResponse(BaseModel):
    data: list[ProjectSearchResult]