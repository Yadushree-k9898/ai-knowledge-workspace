# Audit logs

Audit logs provide an immutable, organization-scoped record of material changes
within the product. Each event captures the acting user or system actor,
organization, action name, resource type and ID, UTC timestamp, and a small
metadata payload describing the relevant mutation. The event stream is append-only:
new rows are written only by the same database transaction that performs the
business change, so failed operations cannot leave success-shaped audit entries,
and committed changes cannot silently omit the corresponding log record.

The system treats the audit log as a compliance and operations trail rather than
an editable data model. There is no update or delete endpoint for audit events,
and rows are not cascade-deleted when their organization is removed. The
organization deletion itself remains visible as a logged event while the
organization becomes unavailable to the scoped API.

The initial event set covers organization lifecycle actions, member-role and
membership changes, invitations, project CRUD, project-document link changes,
comparison creation, and research report lifecycle transitions. Metadata is
limited to fields that explain the change, such as role transitions, project IDs,
counts, or changed attribute names. It must not include document text,
invitation tokens, email addresses in sensitive contexts, authentication
credentials, or access tokens.

Access is restricted to organization owners and admins. The API supports
filtering by action, resource, and time bounds, and it paginates in bounded
offset slices for predictable response sizes. The frontend exposes a read-only
viewer from organization settings.

See [Audit logs API documentation](../api/audit-logs.md).
