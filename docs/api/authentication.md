# Authentication and profiles

Supabase Auth owns credentials, email verification, password reset, Google
OAuth, and browser sessions. FastAPI verifies Supabase access tokens and stores
application profiles. Never put a Supabase service-role key in the frontend.

## Supabase configuration

Set the frontend variables in `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<publishable-anon-key>
```

Set `SUPABASE_JWT_SECRET` for the same Supabase project in
`backend/.env`. For a deployed frontend, set `FRONTEND_ORIGIN` in
`backend/.env` to its exact origin so API CORS allows the app.
Enable email confirmations in Supabase Auth if users must verify ownership of
their email before signing in.
Configure Supabase Auth's own request and email rate limits for sign-in,
sign-up, and password recovery; those browser requests go directly to Supabase
and do not pass through the FastAPI rate limiter.

In Supabase Auth URL Configuration, allow the local callback
`http://localhost:3000/auth/callback` and the production callback
`https://<frontend-host>/auth/callback`. For Google, enable the Google provider
in Supabase and configure its displayed Supabase callback URL in the Google
OAuth client. Restrict the Google OAuth client's authorized JavaScript origins
and redirect URIs to the required application and Supabase URLs.

## Browser flows

* `/signup` creates an email/password identity. When email confirmation is
  enabled, the confirmation link returns to `/auth/callback`; the profile is
  bootstrapped after the authorization code is exchanged.
* `/login` supports email/password and Google. Successful sessions persist in
  the Supabase browser client with PKCE and automatic refresh.
* `/forgot-password` sends a password recovery email; the callback exchanges
  its code and forwards to `/reset-password`, where the user chooses a new
  password.
* `/auth/callback` completes email confirmation, password recovery, or Google
  OAuth, then initializes the application profile.
* Authenticated application routes check the browser session and bootstrap a
  profile if needed. Sign-out clears the Supabase session.
* `/account` reads and updates the application display name and avatar URL.
* Organization invitations can be opened before login, then return to the
  invitation after sign-up/sign-in. The API requires the authenticated email
  to match the invitation recipient before accepting.

## Backend endpoints

The profile endpoints require `Authorization: Bearer <access-token>`:

* `POST /api/v1/auth/bootstrap` creates the application profile idempotently.
* `GET /api/v1/auth/me` returns the current profile and token email.
* `PATCH /api/v1/auth/me` updates display name and avatar URL.
* `DELETE /api/v1/auth/me` permanently deletes the authenticated Supabase
  identity, profile, personal documents, notifications, and organization
  memberships. It is limited to three requests per hour.
* `GET /api/v1/auth/context` returns the profile and organization memberships.

Account deletion requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in
`backend/.env`. The service-role key must remain server-side and must never be
exposed to the frontend. Deletion is blocked while the user owns an
organization or has uploaded documents linked to projects. Transfer ownership
and transfer or unlink those documents first. Project-shared reports,
comparisons, and append-only audit history are retained; removed memberships
are recorded in the organization's audit log.

Profile bootstrap is limited to 10 requests per hour and profile updates to 20
per hour per authenticated user and direct client IP. See
[API rate limits](rate-limits.md) for shared Redis enforcement and all covered
operations.