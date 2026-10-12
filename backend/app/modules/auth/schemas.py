"""
Pydantic schemas for the Auth module.

These define the request/response shapes for all auth endpoints.
Validation rules follow plan.md sections 22-23:
  - display_name: required, 2-100 chars, trimmed
  - avatar_url: optional, valid URL, max 500 chars
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class BootstrapRequest(BaseModel):
    """POST /auth/bootstrap — create profile after first login."""
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's display name",
        examples=["Yadushree"],
    )

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Display name must be at least 2 characters after trimming whitespace.")
        return stripped


class ProfileUpdateRequest(BaseModel):
    """PATCH /auth/me — update profile fields."""
    display_name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="New display name",
    )
    avatar_url: str | None = Field(
        None,
        max_length=500,
        description="URL to avatar image",
    )

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Display name must be at least 2 characters after trimming whitespace.")
        return stripped

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.startswith(("https://", "http://")):
            raise ValueError("Avatar URL must start with https:// or http://")
        return v


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class ProfileResponse(BaseModel):
    """Single profile data returned by GET /auth/me and PATCH /auth/me."""
    id: str
    email: str
    display_name: str
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BootstrapResponse(BaseModel):
    """POST /auth/bootstrap response."""
    user: ProfileResponse
    is_new: bool = Field(
        description="True if the profile was just created, False if it already existed."
    )


class AuthContextOrganization(BaseModel):
    """Organization summary inside the auth context response."""
    id: str
    name: str
    role: str


class AuthContextResponse(BaseModel):
    """GET /auth/context — user profile + their organizations."""
    user: ProfileResponse
    organizations: list[AuthContextOrganization] = []


# ---------------------------------------------------------------------------
# Wrapper to match plan.md { "data": ... } convention
# ---------------------------------------------------------------------------

class DataWrapper(BaseModel):
    """Generic wrapper so responses are always { "data": ... }."""
    data: dict | list | BaseModel
