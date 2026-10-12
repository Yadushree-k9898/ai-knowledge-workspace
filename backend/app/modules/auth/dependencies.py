"""
Auth dependencies — FastAPI dependency injection for authentication.

Provides:
  - get_current_user: verifies JWT, returns user identity dict
  - get_current_profile: verifies JWT + loads profile from DB
  - get_client_ip: extracts client IP for security logging
"""

from fastapi import Depends, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthTokenMissing, AuthTokenInvalid, AuthTokenExpired, ProfileNotFound
from app.core.logging import log_security_event
from app.db.session import get_db
from app.db.models.profile import Profile
from app.modules.auth import repository as repo

security = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """Extract the client's IP address from the request."""
    # Check for proxy headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_request_id(request: Request) -> str | None:
    """Get the request ID set by RequestIDMiddleware."""
    return getattr(request.state, "request_id", None)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> dict:
    """
    Verify the Supabase JWT and return the user's identity.

    Returns a dict with:
      - id: the user's UUID (from 'sub' claim)
      - email: the user's email
      - role: the Supabase role claim
    """
    if credentials is None:
        log_security_event(
            "AUTH_TOKEN_MISSING",
            ip_address=get_client_ip(request),
            request_id=get_request_id(request),
        )
        raise AuthTokenMissing()

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        log_security_event(
            "AUTH_TOKEN_EXPIRED",
            ip_address=get_client_ip(request),
            request_id=get_request_id(request),
        )
        raise AuthTokenExpired()
    except jwt.InvalidTokenError as e:
        log_security_event(
            "AUTH_TOKEN_INVALID",
            ip_address=get_client_ip(request),
            detail=str(e),
            request_id=get_request_id(request),
        )
        raise AuthTokenInvalid(f"Invalid token: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthTokenInvalid("Token missing 'sub' claim.")

    return {
        "id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
    }


def get_current_profile(
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    """
    Verify JWT AND load the user's application profile from DB.

    Raises ProfileNotFound if the user hasn't bootstrapped yet.
    Use this dependency on endpoints that require a fully-set-up user.
    """
    profile = repo.get_profile_by_id(db, user["id"])
    if profile is None:
        log_security_event(
            "PROFILE_NOT_FOUND",
            user_id=user["id"],
            ip_address=get_client_ip(request),
            request_id=get_request_id(request),
        )
        raise ProfileNotFound()
    return profile
