from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.core.config import settings
from app.core.exceptions import AuthTokenInvalid, PermissionDenied
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models.organization import Organization
from app.db.models.organization_invitation import OrganizationInvitation
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.profile import Profile
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.service import bootstrap_user
from app.modules.organizations.service import accept_invitation


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/auth/me",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


def _token(*, role: str = "authenticated") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "user-1",
            "email": "user@example.com",
            "role": role,
            "aud": "authenticated",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )


def test_current_user_requires_authenticated_supabase_role():
    user = get_current_user(
        _request(),
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token()),
    )
    assert user["id"] == "user-1"
    assert user["email"] == "user@example.com"

    with pytest.raises(AuthTokenInvalid):
        get_current_user(
            _request(),
            HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=_token(role="anon"),
            ),
        )


def test_profile_bootstrap_is_idempotent():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=[Profile.__table__])
    db = sessionmaker(bind=engine)()
    try:
        profile, created = bootstrap_user(
            db,
            user_id="user-1",
            email="user@example.com",
            display_name="Researcher",
        )
        existing, created_again = bootstrap_user(
            db,
            user_id="user-1",
            email="user@example.com",
            display_name="Different name",
        )
        assert created is True
        assert created_again is False
        assert existing.id == profile.id
        assert existing.display_name == "Researcher"
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=[Profile.__table__])
        engine.dispose()


def test_invitation_requires_invited_email_and_accepts_case_insensitive_match():
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        OrganizationInvitation.__table__,
        AuditLog.__table__,
    ]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=tables)
    db = sessionmaker(bind=engine)()
    db.add(
        Organization(
            id="org-1",
            name="Research",
            slug="research",
            owner_id="owner-1",
        )
    )
    db.add(
        OrganizationInvitation(
            id="invite-1",
            organization_id="org-1",
            email="invitee@example.com",
            role=OrgRole.MEMBER,
            token="secret-token",
            invited_by="owner-1",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    db.commit()

    try:
        with pytest.raises(PermissionDenied):
            accept_invitation(
                db,
                token="secret-token",
                user_id="wrong-user",
                email="other@example.com",
            )

        member = accept_invitation(
            db,
            token="secret-token",
            user_id="right-user",
            email="INVITEE@example.com",
        )
        assert member.user_id == "right-user"
        assert member.organization_id == "org-1"
        assert member.role == OrgRole.MEMBER
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()
