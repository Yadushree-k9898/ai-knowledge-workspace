"""Email delivery for organization invitations."""

import json
from datetime import timezone
from html import escape
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.organization_invitation import OrganizationInvitation

logger = get_logger("organizations.email")

RESEND_EMAILS_URL = "https://api.resend.com/emails"


def send_invitation_email(
    invitation: OrganizationInvitation,
    organization_name: str,
) -> dict[str, str]:
    """Send an invitation email, returning an explicit delivery status."""
    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
        return {
            "status": "not_configured",
            "message": "Email delivery is not configured. Copy and share the invitation link instead.",
        }

    invitation_url = (
        f"{settings.FRONTEND_ORIGIN.rstrip('/')}/invitations/"
        f"{quote(invitation.token, safe='')}"
    )
    safe_organization = escape(organization_name)
    safe_role = escape(invitation.role.value.lower())
    safe_url = escape(invitation_url, quote=True)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    expires_text = expires_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    safe_expires_text = escape(expires_text)
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [invitation.email],
        "subject": f"Invitation to join {organization_name}",
        "html": (
            f"<p>You have been invited to join <strong>{safe_organization}</strong> "
            f"as a {safe_role}.</p>"
            f'<p><a href="{safe_url}">Accept your invitation</a></p>'
            f"<p>This invitation expires on {safe_expires_text}. Sign in or create an account "
            "with the invited email address to accept it.</p>"
        ),
        "text": (
            f"You have been invited to join {organization_name} as a "
            f"{invitation.role.value.lower()}.\n\n"
            f"Accept your invitation: {invitation_url}\n\n"
            f"This invitation expires on {expires_text}. Sign in or create an account "
            "with the invited email address to accept it."
        ),
    }
    request = Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read())
            if not isinstance(result, dict) or not result.get("id"):
                logger.error("Resend returned an invalid invitation email response.")
                return {
                    "status": "failed",
                    "message": "The email provider returned an invalid response. Copy and share the invitation link instead.",
                }
    except HTTPError as error:
        logger.warning("Resend rejected invitation email with HTTP status %s.", error.code)
        return {
            "status": "failed",
            "message": f"The email provider rejected delivery (HTTP {error.code}). Copy and share the invitation link instead.",
        }
    except (URLError, TimeoutError) as error:
        logger.warning("Could not deliver invitation email: %s", error)
        return {
            "status": "failed",
            "message": "The email provider could not be reached. Copy and share the invitation link instead.",
        }
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        logger.error("Resend returned an unreadable invitation email response: %s", error)
        return {
            "status": "failed",
            "message": "The email provider returned an invalid response. Copy and share the invitation link instead.",
        }

    logger.info("Invitation email sent to %s.", invitation.email)
    return {
        "status": "sent",
        "message": f"Invitation email sent to {invitation.email}.",
    }
