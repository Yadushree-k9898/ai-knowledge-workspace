"""
Auth service — business logic for authentication-related operations.

This layer orchestrates repository calls and enforces business rules
such as idempotent bootstrap and safe account deletion.
"""

from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AccountDeletionBlocked, ExternalServiceError
from app.core.logging import log_security_event, get_logger
from app.db.models.notification import Notification
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember
from app.db.models.project_document import ProjectDocument
from app.db.models.profile import Profile
from app.db.models_legacy import Document, DocumentChunk
from app.modules.audit.service import record_audit_event
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

    try:
        profile = repo.create_profile(db, user_id=user_id, display_name=display_name)
    except IntegrityError:
        db.rollback()
        profile = repo.get_profile_by_id(db, user_id)
        if profile is None:
            raise
        return profile, False
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
    clear_avatar: bool = False,
    ip_address: str | None = None,
) -> Profile:
    """Update the user's profile with any provided fields."""
    updated = repo.update_profile(
        db,
        profile,
        display_name=display_name,
        avatar_url=avatar_url,
        clear_avatar=clear_avatar,
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
    *,
    user_id: str,
    email: str | None,
    ip_address: str | None = None,
) -> None:
    """Remove the user's personal application data and Supabase identity."""
    owns_organization = (
        db.query(Organization.id)
        .filter(Organization.owner_id == user_id)
        .first()
    )
    if owns_organization is not None:
        raise AccountDeletionBlocked(
            "Transfer ownership of all organizations before deleting this account."
        )

    linked_document = (
        db.query(Document.id)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(Document.user_id == user_id)
        .first()
    )
    if linked_document is not None:
        raise AccountDeletionBlocked(
            "Transfer or unlink all project documents uploaded by this account before deleting it."
        )

    try:
        document_ids = [
            row.id
            for row in db.query(Document.id).filter(Document.user_id == user_id).all()
        ]
        if document_ids:
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(document_ids)
            ).delete(synchronize_session=False)
            db.query(Document).filter(Document.id.in_(document_ids)).delete(
                synchronize_session=False
            )

        memberships = (
            db.query(OrganizationMember)
            .filter(OrganizationMember.user_id == user_id)
            .all()
        )
        for membership in memberships:
            record_audit_event(
                db,
                organization_id=membership.organization_id,
                user_id=user_id,
                action="MEMBER_REMOVED",
                resource_type="organization_member",
                resource_id=membership.id,
                metadata={"reason": "ACCOUNT_DELETED"},
            )
            db.delete(membership)

        notification_recipients = Notification.user_id == user_id
        if email:
            notification_recipients = or_(
                notification_recipients,
                (
                    Notification.user_id.is_(None)
                    & (func.lower(Notification.recipient_email) == email.strip().lower())
                ),
            )
        db.query(Notification).filter(notification_recipients).delete(
            synchronize_session=False
        )

        profile = repo.get_profile_by_id(db, user_id)
        if profile is not None:
            repo.delete_profile(db, profile)
        db.flush()
    except SQLAlchemyError:
        db.rollback()
        raise

    try:
        delete_supabase_identity(user_id)
    except ExternalServiceError:
        db.rollback()
        raise

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "Application data cleanup failed after deleting Supabase identity for user %s",
            user_id,
        )
        raise ExternalServiceError(
            "The identity was deleted, but application data cleanup failed. Contact support."
        ) from exc

    log_security_event(
        "ACCOUNT_DELETED",
        user_id=user_id,
        ip_address=ip_address,
        detail="Profile and application data removed.",
    )
    logger.info("Account deleted for user %s", user_id)


def delete_supabase_identity(user_id: str) -> None:
    """Delete an auth identity using the server-side Supabase admin API."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ExternalServiceError(
            "Account deletion is unavailable because the identity provider is not configured."
        )

    url = (
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/"
        f"{quote(user_id, safe='')}"
    )
    request = Request(
        url,
        headers={
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        },
        method="DELETE",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if response.status not in (200, 204):
                raise ExternalServiceError(
                    f"The identity provider returned HTTP {response.status} during account deletion."
                )
    except HTTPError as exc:
        raise ExternalServiceError(
            f"The identity provider rejected account deletion (HTTP {exc.code})."
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise ExternalServiceError(
            "Could not reach the identity provider to delete this account."
        ) from exc
