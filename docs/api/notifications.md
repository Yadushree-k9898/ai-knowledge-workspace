# Notifications

Notifications are private to the authenticated user. Requests require a
Supabase access token:

```http
Authorization: Bearer <access-token>
```

## List notifications

### `GET /api/v1/notifications`

Returns the latest 50 notifications by default. Use `limit` (1–100), `offset`,
and `unread_only` to page or filter the inbox.

```http
GET /api/v1/notifications?unread_only=true&limit=20&offset=0
```

The response is `{ "data": [...] }`. Each notification contains `id`, `type`,
`title`, `message`, optional in-app `link`, `read_at`, and `created_at`.

Pending organization invitation notifications are addressed to the invitation
email. The first authenticated inbox request with a matching email claim
associates the notification with that user; the email address is not returned
in the API response.

## Mark read or unread

### `PATCH /api/v1/notifications/{notification_id}/read`

### `PATCH /api/v1/notifications/{notification_id}/unread`

Both return `{ "data": <notification> }`. A notification owned by another user
is returned as not found.

## Delivered events

* `DOCUMENT_PROCESSED`: document upload and synchronous processing succeeded.
* `DOCUMENT_PROCESSING_FAILED`: parsing failed or the uploaded document
  contained no extractable text.
* `REPORT_READY` / `REPORT_FAILED`: a report generation finished successfully
  or failed.
* `INVITATION_RECEIVED`: an organization invitation was created for the
  recipient's email address.

The inbox is available at `/notifications`.

## Invitation email delivery

When an organization invitation is created, the API also attempts to deliver
an email using Resend. Configure `RESEND_API_KEY` and `RESEND_FROM_EMAIL` in
the backend environment; the sender address must be verified with Resend.
The API key must remain server-side.

The invitation response includes `email_delivery.status` (`sent`,
`not_configured`, or `failed`) and a message. Invitation creation is retained
even if delivery is unavailable, and the response still contains the
invitation token so an administrator can share the link manually.
