"""
Auth repository — database access layer for profiles.

All SQL queries for the Profile table live here.
Business logic belongs in service.py, not here.
"""

from sqlalchemy.orm import Session
from app.db.models.profile import Profile


def get_profile_by_id(db: Session, user_id: str) -> Profile | None:
    """Fetch a profile by its primary key (= Supabase user UUID)."""
    return db.query(Profile).filter(Profile.id == user_id).first()


def create_profile(db: Session, user_id: str, display_name: str) -> Profile:
    """Create a new profile row."""
    profile = Profile(
        id=user_id,
        display_name=display_name,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(
    db: Session,
    profile: Profile,
    *,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> Profile:
    """Update mutable profile fields. Only provided values are changed."""
    if display_name is not None:
        profile.display_name = display_name
    if avatar_url is not None:
        profile.avatar_url = avatar_url

    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile: Profile) -> None:
    """Hard-delete a profile row."""
    db.delete(profile)
    db.commit()
