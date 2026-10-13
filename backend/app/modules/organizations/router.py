"""
Organizations router — API endpoints for organizations, members, and invitations.

Endpoints:
    POST   /api/v1/organizations                              — Create organization
    GET    /api/v1/organizations                              — List user's organizations
    GET    /api/v1/organizations/{organization_id}            — Get organization details
    PATCH  /api/v1/organizations/{organization_id}            — Update organization
    DELETE /api/v1/organizations/{organization_id}            — Delete organization

    GET    /api/v1/organizations/{organization_id}/members              — List members
    PATCH  /api/v1/organizations/{organization_id}/members/{member_id} — Change role
    DELETE /api/v1/organizations/{organization_id}/members/{member_id} — Remove member

    POST   /api/v1/organizations/{organization_id}/invitations — Create invitation
    GET    /api/v1/invitations/{token}                         — Get invitation info
    POST   /api/v1/invitations/{token}/accept                  — Accept invitation
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.organizations import service as org_service
from app.modules.organizations.schemas import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
    UpdateMemberRoleRequest,
    CreateInvitationRequest,
    OrganizationResponse,
    OrganizationWithRoleResponse,
    MemberResponse,
    InvitationResponse,
    InvitationPublicResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Organizations"])


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------

@router.post(
    "/organizations",
    status_code=201,
    summary="Create organization",
    dependencies=[Depends(rate_limit("organization-create", limit=5, window_seconds=3600))],
)
async def create_organization(
    body: CreateOrganizationRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new organization. The authenticated user becomes the OWNER.

    A URL-friendly slug is auto-generated from the name.
    """
    org = org_service.create_organization(db, user_id=user["id"], name=body.name)
    return {
        "data": OrganizationResponse.model_validate(org),
    }


@router.get("/organizations", summary="List organizations")
async def list_organizations(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all organizations the current user belongs to,
    including their role in each.
    """
    rows = org_service.list_user_organizations(db, user_id=user["id"])
    orgs = [
        OrganizationWithRoleResponse(
            id=row["organization"].id,
            name=row["organization"].name,
            slug=row["organization"].slug,
            owner_id=row["organization"].owner_id,
            role=row["role"].value,
            created_at=row["organization"].created_at,
            updated_at=row["organization"].updated_at,
        )
        for row in rows
    ]
    return {"data": orgs}


@router.get("/organizations/{organization_id}", summary="Get organization")
async def get_organization(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get organization details. Caller must be a member.
    """
    # Verify membership via the service helper
    org_service._require_membership(db, organization_id, user["id"])
    org = org_service.get_organization(db, organization_id)
    return {
        "data": OrganizationResponse.model_validate(org),
    }


@router.patch("/organizations/{organization_id}", summary="Update organization")
async def update_organization(
    organization_id: str,
    body: UpdateOrganizationRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update organization details. Requires OWNER or ADMIN role.
    """
    org = org_service.update_organization(
        db,
        org_id=organization_id,
        user_id=user["id"],
        name=body.name,
    )
    return {
        "data": OrganizationResponse.model_validate(org),
    }


@router.delete("/organizations/{organization_id}", status_code=200, summary="Delete organization")
async def delete_organization(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an organization and all associated data. OWNER only.
    """
    org_service.delete_organization(db, org_id=organization_id, user_id=user["id"])
    return {
        "data": {"message": "Organization has been deleted successfully."},
    }


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

@router.get("/organizations/{organization_id}/members", summary="List members")
async def list_members(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all members of the organization. Caller must be a member.
    """
    members = org_service.list_members(db, org_id=organization_id, user_id=user["id"])
    return {
        "data": [MemberResponse.model_validate(m) for m in members],
    }


@router.patch(
    "/organizations/{organization_id}/members/{member_id}",
    summary="Change member role",
)
async def update_member_role(
    organization_id: str,
    member_id: str,
    body: UpdateMemberRoleRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change a member's role. Requires OWNER or ADMIN.
    Cannot change the owner's role.
    """
    member = org_service.update_member_role(
        db,
        org_id=organization_id,
        member_id=member_id,
        user_id=user["id"],
        new_role=body.role,
    )
    return {
        "data": MemberResponse.model_validate(member),
    }


@router.delete(
    "/organizations/{organization_id}/members/{member_id}",
    status_code=200,
    summary="Remove member",
)
async def remove_member(
    organization_id: str,
    member_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a member from the organization.
    OWNER/ADMIN can remove others. Members can remove themselves.
    Owner cannot be removed.
    """
    org_service.remove_member(
        db,
        org_id=organization_id,
        member_id=member_id,
        user_id=user["id"],
    )
    return {
        "data": {"message": "Member has been removed."},
    }


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------

@router.post(
    "/organizations/{organization_id}/invitations",
    status_code=201,
    summary="Create invitation",
    dependencies=[Depends(rate_limit("invitation-create", limit=5, window_seconds=3600))],
)
async def create_invitation(
    organization_id: str,
    body: CreateInvitationRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite a user to join the organization by email.
    Requires OWNER or ADMIN. Returns an invitation with a unique accept token.
    """
    invitation = org_service.create_invitation(
        db,
        org_id=organization_id,
        user_id=user["id"],
        email=body.email,
        role=body.role,
    )
    return {
        "data": InvitationResponse.model_validate(invitation),
    }


@router.get(
    "/invitations/{token}",
    summary="Get invitation info",
    dependencies=[
        Depends(
            rate_limit(
                "invitation-preview",
                limit=30,
                window_seconds=60,
                authenticated=False,
            )
        )
    ],
)
async def get_invitation(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Get public invitation information (what the invitee sees).
    Does NOT require authentication — the token itself is the credential.
    """
    invitation = org_service.get_invitation(db, token)

    # Load the organization name for the public view
    org = org_service.get_organization(db, invitation.organization_id)

    return {
        "data": InvitationPublicResponse(
            organization_name=org.name,
            role=invitation.role.value,
            invited_by=invitation.invited_by,
            expires_at=invitation.expires_at,
            is_expired=invitation.is_expired,
            is_accepted=invitation.is_accepted,
        ),
    }


@router.post(
    "/invitations/{token}/accept",
    status_code=200,
    summary="Accept invitation",
    dependencies=[Depends(rate_limit("invitation-accept", limit=10, window_seconds=3600))],
)
async def accept_invitation(
    token: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept an invitation and join the organization.
    Requires authentication — the accepting user must be logged in.
    """
    member = org_service.accept_invitation(
        db,
        token=token,
        user_id=user["id"],
        email=user.get("email"),
    )
    return {
        "data": MemberResponse.model_validate(member),
    }
