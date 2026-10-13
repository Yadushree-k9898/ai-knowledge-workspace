# Module 1 — Authentication

Supabase Auth is the identity provider for email/password, email verification,
password recovery, Google OAuth, refresh, and sign-out. The Next.js browser
client uses PKCE and persistent sessions; `/auth/callback` exchanges the
one-time code and bootstraps an application profile using the authenticated
Supabase access token.

FastAPI accepts only signed access tokens with the expected audience and
authenticated role, and exposes profile/context operations. Protected frontend
routes require an active Supabase session. Invite acceptance also verifies the
authenticated email matches the invitation recipient.

Permanent account deletion remains disabled until identity removal and
organization/project data retention policies are implemented safely. See
[Authentication API and setup](../api/authentication.md).