"""Request and response schemas for in-app notifications."""

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    link: str | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    data: list[NotificationResponse]


class NotificationEnvelope(BaseModel):
    data: NotificationResponse