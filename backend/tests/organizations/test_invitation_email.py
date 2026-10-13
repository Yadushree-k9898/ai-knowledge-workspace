import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

from app.db.models.organization_member import OrgRole
from app.modules.organizations import email


def _invitation():
    return SimpleNamespace(
        email="invitee@example.com",
        token="token/with-special",
        role=OrgRole.MEMBER,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )


def test_invitation_email_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(email.settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(email.settings, "RESEND_FROM_EMAIL", "")

    result = email.send_invitation_email(_invitation(), "Research")

    assert result["status"] == "not_configured"
    assert "share the invitation link" in result["message"]


def test_invitation_email_sends_escaped_content_and_actual_expiry(monkeypatch):
    monkeypatch.setattr(email.settings, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email.settings, "RESEND_FROM_EMAIL", "Workspace <team@example.com>")
    monkeypatch.setattr(email.settings, "FRONTEND_ORIGIN", "https://workspace.example")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"id":"email-123"}'

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(email, "urlopen", fake_urlopen)

    result = email.send_invitation_email(_invitation(), "<Research & Development>")
    payload = json.loads(captured["request"].data)

    assert result["status"] == "sent"
    assert captured["request"].get_header("Authorization") == "Bearer test-key"
    assert captured["timeout"] == 10
    assert payload["to"] == ["invitee@example.com"]
    assert "token%2Fwith-special" in payload["text"]
    assert "&lt;Research &amp; Development&gt;" in payload["html"]
    assert "expires on " in payload["text"]


def test_invitation_email_reports_provider_rejection(monkeypatch):
    monkeypatch.setattr(email.settings, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email.settings, "RESEND_FROM_EMAIL", "team@example.com")

    def reject_request(_request, timeout):
        raise HTTPError(
            email.RESEND_EMAILS_URL,
            422,
            "Invalid sender",
            None,
            BytesIO(b"provider detail"),
        )

    monkeypatch.setattr(email, "urlopen", reject_request)

    result = email.send_invitation_email(_invitation(), "Research")

    assert result["status"] == "failed"
    assert "HTTP 422" in result["message"]
    assert "share the invitation link" in result["message"]
