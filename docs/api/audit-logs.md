# Organization audit logs

Audit events record important organization and project changes. Events are
written in the same database transaction as the operation that produced them,
and the application exposes no update or delete operation for audit records.

## Access and listing

### `GET /api/v1/organizations/{organization_id}/audit-logs`

Requires a Supabase access token and an `OWNER` or `ADMIN` membership in the
organization. Other members and non-members receive `403`.

Optional query parameters:

* `action`: exact action name.
* `resource_type`: exact resource type.
* `since` and `until`: inclusive ISO-8601 timestamps. `since` must not be later
  than `until`.
* `limit`: 1–100, default 50.
* `offset`: zero or greater, default 0.

Example:

```http
GET /api/v1/organizations/org-id/audit-logs?action=PROJECT_CREATED&limit=20&offset=0
Authorization: Bearer <access-token>
```

Response:

```json
{
  "data": [
    {
      "id": "event-id",
      "organization_id": "org-id",
      "user_id": "actor-id",
      "action": "PROJECT_CREATED",
      "resource_type": "project",
      "resource_id": "project-id",
      "timestamp": "2026-10-12T12:00:00Z",
      "metadata": {}
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 1
  }
}
```

Events are sorted by timestamp descending. The event's `user_id` is the actor
and may be null for system-generated activity. Resource IDs are strings even
when the underlying resource uses a numeric ID.

## Recorded actions

The initial implementation records:

* `ORGANIZATION_CREATED`, `ORGANIZATION_UPDATED`, `ORGANIZATION_DELETED`
* `MEMBER_ROLE_CHANGED`, `MEMBER_REMOVED`
* `INVITATION_CREATED`, `INVITATION_ACCEPTED`
* `PROJECT_CREATED`, `PROJECT_UPDATED`, `PROJECT_DELETED`
* `DOCUMENT_LINKED_TO_PROJECT`, `DOCUMENT_DELETED`
* `COMPARISON_CREATED`
* `REPORT_CREATED`, `REPORT_REGENERATION_REQUESTED`, `REPORT_DELETED`

Metadata is intentionally limited to changed field names, role transitions,
project IDs, and counts. Document contents, invitation email addresses and
tokens, credentials, and access tokens are not copied into audit records.

Audit rows are not foreign-key cascaded when an organization is deleted. This
allows the deletion itself to be recorded; deleted organizations are no longer
available through the organization-scoped API.

The organization audit-log viewer is available from organization settings at
`/organizations/{organization_id}/audit-logs`.
