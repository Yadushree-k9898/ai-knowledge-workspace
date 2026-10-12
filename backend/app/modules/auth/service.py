"""
Auth service — business logic for authentication-related operations.

This layer orchestrates repository calls and enforces business rules
such as idempotent bootstrap and safe account deletion.
"""

from sqlalchemy.orm import Session

from app.core.logging import log_security_event, get_logger
from app.db.models.profile import Profile
from app.modules.auth import repository as repo

logger = get_logger("auth.service")


def bootstrap_user(
    db: Session,
    *,
    user_id: str,
    email: str,
    display_name: str,
    ip_address: str | None = None,
) -> tuple[Profile, bool]:
    """
    Ensure the authenticated user has an application profile.

    This is IDEMPOTENT:
      - If a profile already exists → return it, is_new=False
      - If no profile exists → create it, is_new=True

    Returns (profile, is_new).
    """
    existing = repo.get_profile_by_id(db, user_id)
    if existing:
        logger.info(f"Bootstrap: profile already exists for user {user_id}")
        return existing, False

    profile = repo.create_profile(db, user_id=user_id, display_name=display_name)
    log_security_event(
        "PROFILE_CREATED",
        user_id=user_id,
        ip_address=ip_address,
        detail=f"Profile created for {email}",
    )
    logger.info(f"Bootstrap: new profile created for user {user_id}")
    return profile, True


def get_profile(db: Session, user_id: str) -> Profile | None:
    """Retrieve a user's profile, or None if not bootstrapped yet."""
    return repo.get_profile_by_id(db, user_id)


def update_profile(
    db: Session,
    profile: Profile,
    *,
    display_name: str | None = None,
    avatar_url: str | None = None,
    ip_address: str | None = None,
) -> Profile:
    """Update the user's profile with any provided fields."""
    updated = repo.update_profile(
        db,
        profile,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    log_security_event(
        "PROFILE_UPDATED",
        user_id=profile.id,
        ip_address=ip_address,
        detail=f"Fields updated: display_name={'yes' if display_name else 'no'}, avatar_url={'yes' if avatar_url else 'no'}",
    )
    return updated


def delete_account(
    db: Session,
    profile: Profile,
    *,
    ip_address: str | None = None,
) -> None:
    """
    Delete the user's application data.

    Current scope: profile only.
    TODO: cascade to org memberships, documents, conversations, etc.
    """
    user_id = profile.id
    repo.delete_profile(db, profile)

    log_security_event(
        "ACCOUNT_DELETED",
        user_id=user_id,
        ip_address=ip_address,
        detail="Profile and application data removed.",
    )
    logger.info(f"Account deleted for user {user_id}")
