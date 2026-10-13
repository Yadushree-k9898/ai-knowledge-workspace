# Organization analytics

Get usage counts for an organization the authenticated user belongs to.

All requests require a Supabase access token:

```http
Authorization: Bearer <access-token>
```

## Get analytics

### `GET /api/v1/organizations/{organization_id}/analytics`

Optional query parameters `date_from` and `date_to` accept ISO dates
(`YYYY-MM-DD`) and include both boundary dates. The default range is the last
30 calendar days, including today. Reversed ranges return a validation error.

```http
GET /api/v1/organizations/org-123/analytics?date_from=2026-10-01&date_to=2026-10-12
```

Response:

```json
{
  "data": {
    "organization_id": "org-123",
    "date_from": "2026-10-01",
    "date_to": "2026-10-12",
    "documents_uploaded": 8,
    "documents_processed": null,
    "questions_asked": null,
    "reports_generated": 3,
    "active_users": 4,
    "processing_failures": null,
    "searches": null,
    "average_response_latency_ms": null,
    "ai_usage": null,
    "unavailable_metrics": [
      "documents_processed",
      "questions_asked",
      "processing_failures",
      "searches",
      "average_response_latency_ms",
      "ai_usage"
    ]
  }
}
```

`documents_uploaded` counts distinct documents linked to a project in the
organization and uploaded during the selected range. `reports_generated` counts
reports in `READY` status completed during the range. `active_users` counts
distinct document uploaders, report creators, and comparison creators with
activity during the range.

Metrics returned as `null` are not currently recorded. They are not zero-valued
usage: chat question counts, processing failures, searches, response latency,
document processing outcomes, and AI token usage require telemetry that the
application does not persist yet.
Only organization members can access these analytics.
