# Project document comparisons

Comparisons are asynchronous ARQ jobs. They are available to members of the
project's organization; only owners, admins, and members can add documents or
start comparisons. Documents must be linked to the project first, and only a
document's owner can add it.

Every endpoint requires a Supabase access token:

```http
Authorization: Bearer <access-token>
```

## List project documents

### `GET /api/v1/projects/{project_id}/documents`

Returns documents already linked to the project:

```json
{
  "data": [
    {
      "id": 12,
      "filename": "annual-report.pdf",
      "created_at": "2026-10-12T12:00:00Z",
      "added_at": "2026-10-12T12:30:00Z"
    }
  ]
}
```

## Add an uploaded document to a project

### `POST /api/v1/projects/{project_id}/documents`

The authenticated user must own the document and be a member of the project
organization. Adding the same document again is idempotent.

Request:

```json
{
  "document_id": 12
}
```

## Start a comparison

### `POST /api/v1/projects/{project_id}/comparisons`

Returns `202 Accepted` after the comparison has been persisted and queued.

Request:

```json
{
  "document_ids": [12, 13],
  "instructions": "Compare the financial risks."
}
```

Choose between two and five distinct documents already linked to the project.
Instructions are optional and limited to 5,000 characters. The combined source
text limit is 200,000 characters.

Response:

```json
{
  "data": {
    "id": "comparison-uuid",
    "project_id": "project-uuid",
    "document_ids": [12, 13],
    "document_names": ["2025-report.pdf", "2026-report.pdf"],
    "instructions": "Compare the financial risks.",
    "status": "QUEUED",
    "result": null,
    "error": null,
    "created_at": "2026-10-12T12:40:00Z",
    "updated_at": "2026-10-12T12:40:00Z"
  }
}
```

## Read comparison status or result

### `GET /api/v1/projects/{project_id}/comparisons/{comparison_id}`

Poll this endpoint until `status` becomes `COMPLETED` or `FAILED`. A successful
response has the generated comparison in `data.result`. Failed jobs return a
safe error message in `data.error`.

## List recent comparisons

### `GET /api/v1/projects/{project_id}/comparisons`

Returns up to the 20 most recent comparisons, including status and completed
results.

## Run locally

From the repository root, start Redis:

```powershell
docker compose up -d redis
```

Copy `backend/.env.example` to `backend/.env` and configure the database,
Supabase JWT secret, and Gemini API key. Install `backend/requirements.txt`.
Then, in two terminals with `backend` as the working directory, run:

```powershell
uvicorn app.main:app --reload
```

```powershell
arq app.workers.worker.WorkerSettings
```
