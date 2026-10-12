"""
Pydantic schemas for the Organizations module.

These define the request/response shapes for all organization,
member, and invitation endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.db.models.organization_member import OrgRole


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class CreateOrganizationRequest(BaseModel):
    """POST /organizations — create a new organization."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Organization name",
        examples=["Acme Research"],
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters after trimming.")
        return stripped


class UpdateOrganizationRequest(BaseModel):
    """PATCH /organizations/{id} — update organization details."""
    name: str | None = Field(
        None,
        min_length=2,
        max_length=200,
        description="New organization name",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters after trimming.")
        return stripped


class UpdateMemberRoleRequest(BaseModel):
    """PATCH /organizations/{id}/members/{member_id} — change a member's role."""
    role: OrgRole = Field(
        ...,
        description="New role for the member",
        examples=["MEMBER"],
    )


class CreateInvitationRequest(BaseModel):
    """POST /organizations/{id}/invitations — invite a user."""
    email: str = Field(
        ...,
        max_length=320,
        description="Email address of the person to invite",
        examples=["user@example.com"],
    )
    role: OrgRole = Field(
        default=OrgRole.MEMBER,
        description="Role the invitee will receive",
        examples=["MEMBER"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address.")
        return v


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class OrganizationResponse(BaseModel):
    """Single organization data."""
    id: str
    name: str
    slug: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationWithRoleResponse(BaseModel):
    """Organization data including the current user's role (for list endpoints)."""
    id: str
    name: str
    slug: str
    owner_id: str
    role: str
    created_at: datetime
    updated_at: datetime


class MemberResponse(BaseModel):
    """Organization member data."""
    id: str
    organization_id: str
    user_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class InvitationResponse(BaseModel):
    """Invitation data returned after creation or lookup."""
    id: str
    organization_id: str
    email: str
    role: str
    token: str
    invited_by: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationPublicResponse(BaseModel):
    """
    Public invitation info (what the invitee sees before accepting).
    Does NOT include the full token or internal IDs.
    """
    organization_name: str
    role: str
    invited_by: str
    expires_at: datetime
    is_expired: bool
    is_accepted: bool
