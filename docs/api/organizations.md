# Organizations

## Create invitation

`POST /api/v1/organizations/{organization_id}/invitations` creates an
invitation and attempts to email the invited address through Resend. The
response retains the invitation fields and includes:

```json
{
  "email_delivery": {
    "status": "sent",
    "message": "Invitation email sent to user@example.com."
  }
}
```

Delivery status is `sent`, `not_configured`, or `failed`. A failed email does
not roll back the invitation; use the returned token to share the link
manually. Configure `RESEND_API_KEY` and a verified `RESEND_FROM_EMAIL` in the
backend environment. See [Notifications](./notifications.md) for setup notes.
