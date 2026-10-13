# Module 11 — Analytics

Organization analytics are scoped to the authenticated user's organization
membership and accept an inclusive date range. The current dashboard reports
only values supported by persisted events:

* Distinct documents linked to the organization and uploaded in the period.
* Reports with `READY` status created in the period.
* Distinct users who uploaded a linked document, created a report, or started a
  document comparison in the period.

The endpoint returns `null` plus an `unavailable_metrics` entry for chat
document processing outcomes, document-processing failures, searches, response
latency, and AI usage until those events are persisted. These values must not
be presented as zero.

API details: [Organization analytics](../api/analytics.md).