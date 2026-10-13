# Project research reports

Reports are asynchronous AI jobs created from documents linked to a project.
Project members can view reports; owners, admins, and members can create and
regenerate reports. Only the report creator can delete one. Creating reports
requires a project role that can write project resources.

Requests require a Supabase access token:

```http
Authorization: Bearer <access-token>
```

Supported report types:

* `SUMMARY`
* `COMPETITOR_ANALYSIS`
* `DOCUMENT_REVIEW`
* `RISK_ANALYSIS`
* `RESEARCH_BRIEF`

## Create a report

### `POST /api/v1/projects/{project_id}/reports`

The project must have at least one linked document, and the combined source
text must be no more than 200,000 characters.

```json
{
  "title": "Competitor Analysis",
  "report_type": "COMPETITOR_ANALYSIS",
  "instructions": "Compare pricing and positioning."
}
```

Returns `202 Accepted` with the created report, initially in `QUEUED` status.
Report generation uses all documents linked to the project when the report is
created and records those document IDs as its sources.

## List project reports

### `GET /api/v1/projects/{project_id}/reports`

Returns up to the 50 most recent reports.

## Get a report

### `GET /api/v1/reports/{report_id}`

Poll while the status is `QUEUED` or `GENERATING`. A successful report has
`status: "READY"` and its Markdown text in `content`. A failed report has
`status: "FAILED"` and a safe message in `error`.

## Regenerate a report

### `POST /api/v1/reports/{report_id}/regenerate`

Queues a new generation attempt for a `READY` or `FAILED` report. The same report
record is reused and its previous content is cleared. A report cannot be
regenerated while a worker is already processing it.

## Delete a report

### `DELETE /api/v1/reports/{report_id}`

Deletes the report. Only its creator can perform this action. Success returns
`204 No Content`.

## Local worker

Start Redis using `docker compose up -d redis`, run the FastAPI app, and start
the ARQ worker from the `backend` directory:

```powershell
arq app.workers.worker.WorkerSettings
```