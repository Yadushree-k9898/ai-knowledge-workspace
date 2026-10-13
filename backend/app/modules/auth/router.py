"""
Auth router — API endpoints for authentication and profile management.

Endpoints:
    GET    /api/v1/auth/me          — Get current user's profile
    POST   /api/v1/auth/bootstrap   — Create profile after first login (idempotent)
    PATCH  /api/v1/auth/me          — Update profile
    DELETE /api/v1/auth/me          — Account deletion (currently unavailable)
    GET    /api/v1/auth/context     — Get user profile + organizations
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.db.models.profile import Profile
from app.modules.auth.dependencies import (
    get_current_user,
    get_current_profile,
    get_client_ip,
)
from app.modules.auth.schemas import (
    BootstrapRequest,
    BootstrapResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    AuthContextResponse,
    AuthContextOrganization,
)
from app.modules.auth import service as auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get("/me", summary="Get current user profile")
async def get_me(
    profile: Profile = Depends(get_current_profile),
    user: dict = Depends(get_current_user),
):
    """
    Return the authenticated user's application profile.

    Requires: valid JWT + bootstrapped profile.
    """
    return {
        "data": ProfileResponse(
            id=profile.id,
            email=user["email"],
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    }


# ---------------------------------------------------------------------------
# POST /auth/bootstrap
# ---------------------------------------------------------------------------

@router.post(
    "/bootstrap",
    status_code=200,
    summary="Bootstrap user profile",
    dependencies=[Depends(rate_limit("profile-bootstrap", limit=10, window_seconds=3600))],
)
async def bootstrap(
    body: BootstrapRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ensure the authenticated user has an application profile.

    This endpoint is **idempotent**:
    - First call → creates the profile, returns `is_new: true`
    - Subsequent calls → returns existing profile, `is_new: false`

    Should be called by the frontend immediately after signup/login.
    """
    profile, is_new = auth_service.bootstrap_user(
        db,
        user_id=user["id"],
        email=user["email"],
        display_name=body.display_name,
        ip_address=get_client_ip(request),
    )

    return {
        "data": BootstrapResponse(
            user=ProfileResponse(
                id=profile.id,
                email=user["email"],
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            ),
            is_new=is_new,
        )
    }


# ---------------------------------------------------------------------------
# PATCH /auth/me
# ---------------------------------------------------------------------------

@router.patch(
    "/me",
    summary="Update profile",
    dependencies=[Depends(rate_limit("profile-update", limit=20, window_seconds=3600))],
)
async def update_me(
    body: ProfileUpdateRequest,
    request: Request,
    profile: Profile = Depends(get_current_profile),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile fields.

    Only provided fields are changed; omitted fields keep their current value.
    """
    updated = auth_service.update_profile(
        db,
        profile,
        display_name=body.display_name,
        avatar_url=body.avatar_url,
        clear_avatar=(
            "avatar_url" in body.model_fields_set and body.avatar_url is None
        ),
        ip_address=get_client_ip(request),
    )

    return {
        "data": ProfileResponse(
            id=updated.id,
            email=user["email"],
            display_name=updated.display_name,
            avatar_url=updated.avatar_url,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    }


# ---------------------------------------------------------------------------
# DELETE /auth/me
# ---------------------------------------------------------------------------

@router.delete(
    "/me",
    status_code=501,
    responses={501: {"description": "Full account deletion is not implemented."}},
    summary="Delete account",
)
async def delete_me(
    user: dict = Depends(get_current_user),
):
    """
    Delete the current user's application profile and all associated data.

    **This action is irreversible.**

    Note: Supabase Auth identity deletion should be handled
    separately on the frontend via supabase.auth.admin.deleteUser().
    """
    _ = user
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account deletion is unavailable until full identity and data cleanup is implemented.",
    )


# ---------------------------------------------------------------------------
# GET /auth/context
# ---------------------------------------------------------------------------

@router.get("/context", summary="Get auth context")
async def get_context(
    profile: Profile = Depends(get_current_profile),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the user's profile and their organization memberships.

    Used by the frontend to initialise the application state after login.
    """
    from app.modules.organizations import repository as org_repo

    org_rows = org_repo.get_organizations_for_user(db, user["id"])
    org_list = [
        AuthContextOrganization(
            id=row["organization"].id,
            name=row["organization"].name,
            role=row["role"].value,
        )
        for row in org_rows
    ]

    context = AuthContextResponse(
        user=ProfileResponse(
            id=profile.id,
            email=user["email"],
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        ),
        organizations=org_list,
    )

    return {"data": context}
