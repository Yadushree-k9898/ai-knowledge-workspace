# Documents API

Documents can be uploaded into a project, listed within that project, and
removed from a project without deleting the underlying document or its chunks.
Project operations require organization membership; upload and removal require
at least the `MEMBER` role.

## Upload a project document

```http
POST /api/v1/projects/{project_id}/documents
Authorization: Bearer <access-token>
Content-Type: multipart/form-data
```

Form field:

| Field | Type | Required |
| --- | --- | --- |
| `file` | PDF, TXT, Markdown, CSV, or JSON file | Yes |

The API extracts text, generates embeddings, links the document to the project,
and records an audit event in the same database transaction.

## List project documents

```http
GET /api/v1/projects/{project_id}/documents
Authorization: Bearer <access-token>
```

Returns the project's linked documents, newest links first. The response
includes each document's ID, filename, creation time, and project-link time.

## Remove a document from a project

```http
DELETE /api/v1/projects/{project_id}/documents/{document_id}
Authorization: Bearer <access-token>
```

This removes only the project link. It intentionally preserves the document
and its chunks, so other project links and the uploader's stored document are
not deleted.

The user-scoped legacy endpoints remain available:

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/`
- `DELETE /api/v1/documents/{document_id}`