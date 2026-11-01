# Delivery Roadmap and Verification Gates

This document tracks completion against `plan.md`. A module is not complete merely because routes or UI files exist: it must pass authorization, persistence, failure-path, and end-to-end checks.

## Gate 0 — Repository and local development foundation

- [x] Document architecture, environment variables, and local setup.
- [x] Add backend container definition.
- [x] Add local PostgreSQL/pgvector and Redis Compose services.
- [x] Add backend pytest configuration.
- [x] Add frontend ESLint configuration.
- [ ] Run CI successfully against the current branch.
- [ ] Confirm generated build artifacts and secrets are excluded from Git.

## Gate 1 — Identity, organizations, and projects

- [ ] Verify JWT signature, issuer, audience, expiry, and subject validation.
- [ ] Verify user identity is derived only from the verified token.
- [ ] Verify bootstrap idempotency and profile update/delete behavior.
- [ ] Verify organization membership and role matrix for every mutation.
- [ ] Verify invitation expiry, single-use acceptance, and email matching.
- [ ] Verify project access is scoped through organization membership.
- [x] Add migration-managed schema changes; do not rely on production `create_all()`.
- [ ] Add integration tests for owner, admin, member, viewer, and outsider roles.

## Gate 2 — Document ingestion

- [ ] Verify file type, size, filename, and content validation.
- [ ] Verify storage upload and database record consistency.
- [ ] Verify background job creation, retry behavior, and duplicate delivery safety.
- [ ] Verify extraction, chunking, embedding dimensions, and page metadata.
- [ ] Verify failed jobs expose safe errors and can be retried.
- [ ] Verify unlink/delete behavior does not remove shared content unexpectedly.

**Current Gate 2 implementation:** project uploads now persist a `PENDING` job and return HTTP 202; an ARQ worker performs extraction, chunking, and embedding; status and retry endpoints are available. The original synchronous service remains for compatibility. Uploaded bytes are temporarily stored in PostgreSQL with a 10 MB limit. Production object storage, Redis-outage recovery automation, duplicate-delivery tests, and full provider-backed integration verification remain open.

## Gate 3 — Search and grounded chat

- [ ] Verify vector search uses project/document scope after authorization.
- [ ] Add hybrid keyword + vector retrieval and ranking evaluation.
- [ ] Verify prompt construction resists instructions contained in retrieved documents.
- [ ] Verify insufficient evidence produces an explicit uncertainty response.
- [ ] Persist messages and source references atomically.
- [ ] Verify citations resolve to the exact source document and page/chunk.

## Gate 4 — Reports and comparisons

- [ ] Verify report/comparison jobs are queued, idempotent, and recoverable.
- [ ] Verify all source documents belong to the authorized project.
- [ ] Persist citations with generated content.
- [ ] Add status, retry, cancellation, and failure-path tests.

## Gate 5 — Analytics, notifications, and audit

- [ ] Add event telemetry for search, chat, processing, response latency, and AI usage.
- [ ] Keep untracked metrics explicitly unavailable rather than reporting false zeroes.
- [ ] Verify notification recipient scoping and read/unread transitions.
- [ ] Verify audit records are immutable from normal user APIs and contain no secrets.

## Gate 6 — Production readiness

- [x] Replace startup-time `Base.metadata.create_all()` with Alembic migrations.
- [ ] Add readiness checks for PostgreSQL, Redis, and required provider configuration.
- [ ] Configure production CORS, HTTPS, secret management, and rate limiting.
- [ ] Add structured logs, request IDs, error monitoring, and worker health checks.
- [ ] Add backup/restore procedure and retention policy.
- [ ] Run dependency/security scans and resolve high/critical findings.
- [ ] Perform load tests for upload, retrieval, and concurrent chat.
- [ ] Publish architecture, data-flow, ER, and deployment diagrams.

## Verification record

| Check | Result |
|---|---|
| Backend pytest on project-completion branch | Passing on earlier async-ingestion commits; latest worker tests are running |
| Frontend lint/build on project-completion branch | Passing on latest completed frontend run |
| PostgreSQL + pgvector migration upgrade/downgrade/re-upgrade | Passing on earlier migration runs; latest run pending |\n| Supabase/Redis/Gemini end-to-end integration | Requires configured credentials/services |

## Completion rule

Only mark a checkbox complete after the corresponding automated test or documented manual verification has passed. CI green is necessary but not sufficient for production readiness.
