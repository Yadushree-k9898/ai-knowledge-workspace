"""
Application-wide exception classes and error response helpers.

Provides a consistent error response format across all modules:
    {
        "error": {
            "code": "PROFILE_NOT_FOUND",
            "message": "Profile does not exist."
        }
    }
"""

from fastapi import HTTPException, status


# ---------------------------------------------------------------------------
# Base Application Error
# ---------------------------------------------------------------------------

class AppError(HTTPException):
    """
    Base error for all application-specific HTTP errors.
    Subclass this for domain errors that need a machine-readable error code.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ) -> None:
        self.code = code
        super().__init__(
            status_code=status_code,
            detail={"error": {"code": code, "message": message}},
        )


# ---------------------------------------------------------------------------
# Authentication / Authorization Errors
# ---------------------------------------------------------------------------

class AuthTokenMissing(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_TOKEN_MISSING",
            message="Authorization header is missing.",
        )


class AuthTokenInvalid(AppError):
    def __init__(self, detail: str = "Token is invalid.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_TOKEN_INVALID",
            message=detail,
        )


class AuthTokenExpired(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_TOKEN_EXPIRED",
            message="Token has expired.",
        )


class ProfileNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROFILE_NOT_FOUND",
            message="Profile does not exist. Call POST /auth/bootstrap first.",
        )


class ProfileAlreadyExists(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="PROFILE_ALREADY_EXISTS",
            message="Profile already exists for this user.",
        )


# ---------------------------------------------------------------------------
# Generic Resource Errors
# ---------------------------------------------------------------------------

class ResourceNotFound(AppError):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} does not exist.",
        )


class PermissionDenied(AppError):
    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=detail,
        )


class ValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=detail,
        )


# ---------------------------------------------------------------------------
# Organization Errors
# ---------------------------------------------------------------------------

class OrganizationNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORGANIZATION_NOT_FOUND",
            message="Organization does not exist.",
        )


class MemberNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEMBER_NOT_FOUND",
            message="Member does not exist in this organization.",
        )


class AlreadyMember(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="ALREADY_MEMBER",
            message="User is already a member of this organization.",
        )


class SlugConflict(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="SLUG_CONFLICT",
            message="An organization with this slug already exists.",
        )


class InvitationNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="INVITATION_NOT_FOUND",
            message="Invitation does not exist.",
        )


class InvitationExpired(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_410_GONE,
            code="INVITATION_EXPIRED",
            message="This invitation has expired.",
        )


class InvitationAlreadyAccepted(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="INVITATION_ALREADY_ACCEPTED",
            message="This invitation has already been accepted.",
        )


class CannotRemoveOwner(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CANNOT_REMOVE_OWNER",
            message="The organization owner cannot be removed.",
        )
