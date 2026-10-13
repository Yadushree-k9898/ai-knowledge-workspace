from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ConversationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty.")
        return value


class ConversationSummaryResponse(BaseModel):
    id: str
    project_id: str
    created_by: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    id: str
    conversation_id: str
    user_id: str | None
    role: Literal["USER", "ASSISTANT"]
    content: str
    sources: list[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    conversation: ConversationSummaryResponse
    messages: list[ConversationMessageResponse]


class ConversationListEnvelope(BaseModel):
    data: list[ConversationSummaryResponse]


class ConversationDetailEnvelope(BaseModel):
    data: ConversationDetailResponse