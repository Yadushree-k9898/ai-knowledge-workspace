# AI Knowledge & Research Workspace

## Master System Design Plan

We are designing this as a **production-style modular SaaS application**, not a simple RAG demo.

The product will allow organizations to:

* create projects
* upload documents
* process and index those documents
* search their knowledge
* ask AI questions
* receive answers with citations
* compare documents
* generate research reports
* collaborate through organization/project permissions
* view usage and system activity

The architecture will start as a **modular monolith** so it is understandable and maintainable, while still using asynchronous workers where they provide a real benefit.

---

# 1. Entire System — High-Level Architecture

```text
                              INTERNET
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     Browser     │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │ Next.js Frontend│
                         │ React + JS      │
                         └───────┬─────────┘
                                 │
                  ┌──────────────┼──────────────┐
                  │                              │
                  ▼                              ▼
          ┌───────────────┐              ┌──────────────┐
          │ Supabase Auth │              │ FastAPI API  │
          └───────────────┘              └──────┬───────┘
                                                │
                         ┌──────────────────────┼─────────────────────┐
                         │                      │                     │
                         ▼                      ▼                     ▼
                  ┌──────────────┐       ┌────────────┐       ┌────────────┐
                  │ PostgreSQL   │       │   Redis    │       │  Supabase  │
                  │ + pgvector   │       │Queue/Cache │       │  Storage   │
                  └──────────────┘       └─────┬──────┘       └────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ ARQ Worker  │
                                        └──────┬──────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ Document / AI   │
                                      │ Processing      │
                                      └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ Gemini API      │
                                      └─────────────────┘
```

---

# 2. System Modules

We will design the system as these logical modules:

```text
01. Authentication
02. Organizations & Members
03. Projects
04. Documents
05. Document Processing
06. Search
07. AI Chat
08. Research Reports
09. Collaboration
10. Analytics
11. Notifications
12. Audit & Administration
13. Infrastructure / DevOps
```

Each module gets its own:

```text
Requirements
↓
Database entities
↓
API endpoints
↓
Request/response models
↓
Business logic
↓
Data flow
↓
Security rules
↓
Error handling
↓
Tests
```

---

# 3. Global API Rules

Before designing individual modules, we establish conventions.

## Base URL

```text
/api/v1
```

Example:

```text
/api/v1/projects
```

---

## Authentication

Protected endpoints receive:

```http
Authorization: Bearer <access_token>
```

The backend gets the authenticated user's identity from the verified token.

We will **never trust**:

```json
{
  "user_id": "123"
}
```

from the request body to determine who the user is.

The authenticated user comes from the token.

---

## Response format

Successful responses should be predictable.

Example:

```json
{
  "data": {
    "id": "project_123",
    "name": "Competitor Research"
  }
}
```

For lists:

```json
{
  "data": [
    {
      "id": "project_123",
      "name": "Competitor Research"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 42
  }
}
```

Errors:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project does not exist."
  }
}
```

---

# 4. Global HTTP Status Conventions

```text
200 OK
201 Created
204 No Content

400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests

500 Internal Server Error
```

We won't randomly return different formats for different endpoints.

---

# 5. Global Data Flow

Almost every request follows:

```text
Browser
  ↓
Next.js
  ↓
HTTP request
  ↓
FastAPI
  ↓
Authentication middleware
  ↓
Authorization check
  ↓
Validation
  ↓
Business logic
  ↓
Database / Redis / external service
  ↓
Response
  ↓
Next.js
  ↓
User
```

For long-running tasks:

```text
Browser
  ↓
FastAPI
  ↓
Create DB job
  ↓
Push Redis job
  ↓
Return 202 / processing state
  ↓
Worker processes
  ↓
Update database
  ↓
Frontend polls or receives update
```

---

# 6. Data Ownership Rules

We need strict ownership boundaries.

```text
Organization
    ↓
Projects
    ↓
Documents
    ↓
Chunks
```

A user can only access resources through a valid membership.

Example:

```text
User A
  ↓
Organization A
  ↓
Project A
  ↓
Document A
```

User A must not be able to access:

```text
Organization B
Project B
Document B
```

just because they know the ID.

Every protected resource is checked against the authenticated user's permissions.

---

# 7. Main Database Model

At a high level:

```text
auth.users
     │
     ▼
profiles
     │
     ▼
organization_members
     │
     ▼
organizations
     │
     ▼
projects
     │
     ├───────────────┐
     ▼               ▼
documents       conversations
     │               │
     ▼               ▼
document_chunks   messages
     │               │
     ▼               ▼
 embeddings      message_sources

projects
   │
   ▼
research_reports
```

We will add supporting tables such as:

```text
organization_invitations
document_jobs
audit_logs
notifications
```

as those modules are designed.

---

# 8. Module 1 — Authentication

## Purpose

Authentication answers:

> "Who are you?"

Authorization answers:

> "What are you allowed to do?"

We will keep those concepts separate.

For identity, we will use:

**Supabase Auth**

For application authorization:

**FastAPI + PostgreSQL**

---

# 9. Authentication Responsibilities

Authentication needs to support:

```text
1. Sign up
2. Email verification
3. Login
4. Logout
5. Session handling
6. Access-token verification
7. Password reset
8. Password change
9. Get current user
10. Update profile
11. Account deletion
```

Organization invitations and membership will use authentication but belong mainly to the **Organizations** module.

---

# 10. Authentication Architecture

```text
                    USER
                      │
                      ▼
              ┌──────────────┐
              │   Next.js    │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ Supabase Auth│
              └──────┬───────┘
                     │
             access token/session
                     │
                     ▼
              ┌──────────────┐
              │   FastAPI    │
              └──────┬───────┘
                     │
              verify JWT
                     │
                     ▼
              authenticated user
                     │
                     ▼
              authorization
                     │
                     ▼
              application logic
```

Important:

**Supabase Auth stores/manages passwords and identity.**

Our PostgreSQL application tables do **not** store passwords.

---

# 11. Authentication Database

## `auth.users`

Managed by Supabase.

We don't manually create password records here.

It represents the authenticated identity.

Conceptually:

```text
id
email
created_at
...
```

---

## `profiles`

Our application's user profile.

```text
profiles
──────────────
id              UUID  PK
display_name    TEXT
avatar_url      TEXT nullable
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

`profiles.id` corresponds to the authenticated user's ID.

We do not need to duplicate every field from Supabase Auth.

---

# 12. Authentication API Surface

There are two kinds of operations.

### A. Identity operations

Handled by Supabase Auth:

```text
Sign up
Login
Logout
Password reset
Password update
Email verification
Session refresh
```

### B. Application authentication APIs

Handled by our FastAPI application:

```text
GET   /api/v1/auth/me
POST  /api/v1/auth/bootstrap
PATCH /api/v1/auth/me
DELETE /api/v1/auth/me
GET   /api/v1/auth/context
```

This separation is deliberate.

---

# 13. Signup Flow

### User action

User enters:

```text
Name
Email
Password
```

Frontend validates basic requirements.

Then:

```text
Next.js
   ↓
Supabase Auth signUp
   ↓
auth.users
   ↓
Verification email
```

After verification:

```text
User logs in
   ↓
Supabase returns session
   ↓
Next.js obtains access token
   ↓
FastAPI request
   ↓
Authorization header
   ↓
FastAPI verifies token
```

---

# 14. Signup Request

Conceptually:

```json
{
  "email": "user@example.com",
  "password": "strong-password",
  "display_name": "Yadushree"
}
```

The actual signup operation is sent to Supabase Auth rather than our own PostgreSQL password table.

---

# 15. Password Rules

We should enforce:

```text
Minimum length
Password confirmation
Reject obviously weak passwords
```

We should never:

```text
log passwords
store passwords in our DB
return passwords in API responses
send passwords to logs
```

---

# 16. Email Verification Flow

```text
Signup
  ↓
User created
  ↓
Verification email
  ↓
User clicks link
  ↓
Email becomes verified
  ↓
User can access application
```

The exact verification behavior will follow the Supabase Auth configuration.

---

# 17. Login Flow

```text
User enters email/password
        ↓
Next.js
        ↓
Supabase Auth
        ↓
Credentials verified
        ↓
Session created
        ↓
Access token
        ↓
Frontend calls FastAPI
        ↓
FastAPI verifies token
        ↓
User authenticated
```

---

# 18. What is inside the access token?

We should treat the token as a **signed identity assertion**, not as arbitrary user input.

Our backend primarily needs information such as:

```text
user ID / subject
expiration
issuer
audience
```

The backend verifies the token signature and important claims.

We should **not trust** a client-supplied:

```text
user_id
organization_id
role
```

without checking them against our database and/or verified claims.

---

# 19. `GET /api/v1/auth/me`

### Purpose

Return the currently authenticated user's application profile.

### Request

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### No body.

### Response

```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Yadushree",
    "avatar_url": null,
    "email_verified": true,
    "created_at": "2026-09-22T10:00:00Z"
  }
}
```

### Backend flow

```text
Request
 ↓
Extract Bearer token
 ↓
Verify JWT
 ↓
Get user ID
 ↓
Find profile
 ↓
Return profile
```

### Errors

```text
401 AUTH_TOKEN_MISSING
401 AUTH_TOKEN_INVALID
401 AUTH_TOKEN_EXPIRED
404 PROFILE_NOT_FOUND
```

---

# 20. `POST /api/v1/auth/bootstrap`

This is useful immediately after signup/login.

### Purpose

Make sure the application has the user's required application-level records.

For example:

```text
Supabase identity exists
        ↓
Profile exists?
        ↓
No → create profile
Yes → return existing profile
```

### Request

```json
{
  "display_name": "Yadushree"
}
```

### Response

```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "display_name": "Yadushree"
    },
    "onboarding": {
      "completed": false
    }
  }
}
```

This endpoint should be **idempotent**.

Calling it twice should not create duplicate profiles.

---

# 21. Why Bootstrap?

Because identity and application data are different.

```text
Supabase
    ↓
"I know this person exists."

Our DB
    ↓
"I know this person's application profile."
```

This gives us a clean boundary between authentication infrastructure and our product.

---

# 22. `PATCH /api/v1/auth/me`

### Purpose

Update user profile.

### Request

```json
{
  "display_name": "New Name",
  "avatar_url": "https://..."
}
```

The user ID comes from the verified token.

There is **no**:

```json
{
  "user_id": "..."
}
```

in the request.

### Response

```json
{
  "data": {
    "id": "uuid",
    "display_name": "New Name",
    "avatar_url": "https://..."
  }
}
```

---

# 23. Validation

For `display_name`:

```text
Required? yes
Minimum length
Maximum length
Trim whitespace
Reject invalid values
```

For avatar:

```text
Valid URL
Maximum length
Allowed schemes
```

We'll implement these rules through **Pydantic**.

---

# 24. Password Reset

This is primarily a Supabase Auth operation.

Flow:

```text
User clicks "Forgot password"
        ↓
Enters email
        ↓
Supabase sends reset email
        ↓
User clicks link
        ↓
Reset session
        ↓
New password
```

Important security rule:

We should avoid revealing whether an email exists.

Instead of:

```text
"That email does not exist."
```

return a generic message such as:

```text
"If an account exists for this email, a reset link has been sent."
```

This prevents account enumeration.

---

# 25. Password Change

Authenticated user:

```text
User
 ↓
Current authenticated session
 ↓
New password
 ↓
Supabase Auth
 ↓
Password updated
```

Our application database never receives or stores the raw password.

---

# 26. Logout

Logout should invalidate the application's client session through Supabase Auth.

Flow:

```text
User clicks logout
       ↓
Next.js
       ↓
Supabase signOut
       ↓
Session removed
       ↓
Redirect to login
```

FastAPI doesn't need to maintain its own session store in this architecture.

That keeps our system simpler.

---

# 27. Account Deletion

This is a destructive operation.

Flow:

```text
User requests deletion
       ↓
Re-authentication / confirmation
       ↓
Supabase identity deletion
       ↓
Application data cleanup
       ↓
Storage cleanup
```

We need to decide whether:

```text
Delete everything immediately
```

or:

```text
soft-delete first
```

For the first version, we can implement controlled deletion with clear cascading rules.

This needs to be designed carefully because a user may belong to organizations.

---

# 28. Authentication Context

We need more than just:

```text
Who am I?
```

The frontend also needs:

```text
Which organizations am I in?
What roles do I have?
Which organization is active?
```

Therefore:

## `GET /api/v1/auth/context`

Response could be:

```json
{
  "data": {
    "user": {
      "id": "user-123",
      "email": "user@example.com",
      "display_name": "Yadushree"
    },
    "organizations": [
      {
        "id": "org-1",
        "name": "Acme",
        "role": "OWNER"
      },
      {
        "id": "org-2",
        "name": "Research Team",
        "role": "MEMBER"
      }
    ]
  }
}
```

This lets the frontend initialize the user's workspace.

---

# 29. Authentication vs Authorization

This distinction needs to be very clear.

### Authentication

```text
Are you Yadushree?
```

JWT verifies identity.

### Authorization

```text
Are you allowed to delete this project?
```

Database membership + role + permission checks determine that.

Example:

```text
Authenticated user
       ↓
User ID = 123
       ↓
Project ID = 456
       ↓
Find project organization
       ↓
Find organization_members
       ↓
Check role
       ↓
ALLOW / DENY
```

---

# 30. Roles

Initial roles:

```text
OWNER
ADMIN
MEMBER
VIEWER
```

Example:

| Action              | Owner |       Admin | Member | Viewer |
| ------------------- | ----: | ----------: | -----: | -----: |
| View project        |     ✅ |           ✅ |      ✅ |      ✅ |
| Search              |     ✅ |           ✅ |      ✅ |      ✅ |
| Ask AI              |     ✅ |           ✅ |      ✅ |      ✅ |
| Upload docs         |     ✅ |           ✅ |      ✅ |      ❌ |
| Delete docs         |     ✅ |           ✅ |     ✅* |      ❌ |
| Invite members      |     ✅ |           ✅ |      ❌ |      ❌ |
| Manage billing      |     ✅ | maybe later |      ❌ |      ❌ |
| Delete organization |     ✅ |           ❌ |      ❌ |      ❌ |

`*` exact permissions will be finalized in the Organizations module.

We should not hardcode every permission into frontend logic.

The backend is authoritative.

---

# 31. Authentication Middleware

Every protected FastAPI endpoint will go through something like:

```text
Request
 ↓
Authorization header
 ↓
Extract bearer token
 ↓
Verify JWT
 ↓
Get user ID
 ↓
Load authenticated user context
 ↓
Endpoint
```

Conceptually:

```python
current_user = get_current_user(request)
```

Then an endpoint can use:

```python
current_user.id
```

instead of trusting a request body.

---

# 32. Authorization Middleware / Dependency

Authentication alone is not enough.

For organization-scoped endpoints:

```python
require_org_member(
    user_id=current_user.id,
    organization_id=organization_id
)
```

For role-restricted endpoints:

```python
require_role(
    user_id=current_user.id,
    organization_id=organization_id,
    allowed_roles=["OWNER", "ADMIN"]
)
```

This keeps permission checks centralized instead of writing them inconsistently in every endpoint.

---

# 33. Authentication Security Rules

We will enforce:

```text
1. Passwords never stored in our DB
2. Service-role keys never go to browser
3. Access tokens always verified
4. Expired tokens rejected
5. User ID comes from token
6. Organization access comes from DB
7. Roles are checked server-side
8. Generic password-reset responses
9. No sensitive data in logs
10. Rate limiting on sensitive operations
11. HTTPS everywhere outside local development
12. Secrets in environment variables
```

---

# 34. Authentication Rate Limiting

Sensitive actions should be protected from abuse.

Email/password sign-in, signup, and password recovery are sent directly from
the browser to Supabase Auth. Their limits must be configured in Supabase; they
do not pass through FastAPI. FastAPI uses shared Redis fixed-window limits for
backend operations:

```text
organization creation       5 / hour
project creation           20 / hour
invitation creation         5 / hour
invitation preview         30 / minute (IP only)
invitation acceptance      10 / hour
profile bootstrap          10 / hour
profile update             20 / hour
document upload            20 / hour
comparison creation        10 / hour
report creation            10 / hour
report regeneration        10 / hour
```

Authenticated operations enforce both per-user and per-IP counters atomically;
public invitation previews use the direct connection IP. Keys hash identity
values. Requests over the limit return `429` and `Retry-After`. If Redis is
unavailable, these sensitive operations fail with `503` rather than silently
bypassing the limit. Deployments behind a proxy must apply IP-based limits at
the trusted edge; arbitrary forwarded-IP headers are not trusted by the API.

See [Rate limiting API notes](docs/api/rate-limits.md).

---

# 35. Authentication Logging

We should log security events, not passwords or tokens.

Good:

```text
LOGIN_SUCCESS
LOGIN_FAILURE
PASSWORD_RESET_REQUESTED
PASSWORD_CHANGED
PROFILE_UPDATED
ACCOUNT_DELETED
```

Example:

```json
{
  "event": "LOGIN_SUCCESS",
  "user_id": "uuid",
  "timestamp": "..."
}
```

Never:

```json
{
  "password": "..."
}
```

or:

```json
{
  "access_token": "..."
}
```

---

# 36. Audit Logs

Organization audit logs are persisted for key user-initiated changes:

```text
user_id
organization_id
action
resource_type
resource_id
timestamp
metadata
```

The authenticated audit-log endpoint is restricted to organization owners and
admins. Events are ordered newest-first and can be filtered by action and
resource type, with bounded pagination. Event metadata contains only
action-specific identifiers and changed-field/role information; it must not
include document content, invitation tokens, credentials, or access tokens.

Events are added to the same database transaction as the operation they
describe. The event table intentionally does not cascade-delete with the
organization, so organization deletion itself can be recorded. The initial
event set includes organization, membership, invitation, project, project
document-link, comparison, and report changes.

```text
GET /api/v1/organizations/{organization_id}/audit-logs
```

See [Audit logs API documentation](docs/api/audit-logs.md).

---

# 37. Authentication Test Cases

Before considering Authentication finished, we should test:

### Signup

```text
valid signup
invalid email
weak password
duplicate email
```

### Verification

```text
unverified user
verified user
expired verification link
```

### Login

```text
correct credentials
wrong password
unknown email
expired session
malformed token
```

### Authorization

```text
valid user
unauthenticated user
wrong organization
wrong role
```

### Profile

```text
update valid profile
invalid profile
unauthorized update
```

### Security

```text
can't access another user's data
can't spoof user_id
can't spoof organization membership
can't use expired token
can't use invalid token
```

That last group is particularly important.

---

# 38. Authentication Final Data Flow

### Normal request

```text
Browser
  ↓
Next.js
  ↓
Bearer access token
  ↓
FastAPI
  ↓
JWT verification
  ↓
current_user
  ↓
organization membership
  ↓
role/permission check
  ↓
business logic
  ↓
database
  ↓
response
```

### Signup

```text
Browser
  ↓
Next.js
  ↓
Supabase Auth
  ↓
Identity created
  ↓
Email verification
  ↓
Login
  ↓
Access token
  ↓
FastAPI bootstrap
  ↓
Profile created
  ↓
Application ready
```

### Password reset

```text
Forgot password
  ↓
Supabase Auth
  ↓
Reset email
  ↓
User verifies
  ↓
New password
```

---

# 39. Authentication APIs — Final List

### Application APIs

```text
GET    /api/v1/auth/me
POST   /api/v1/auth/bootstrap
PATCH  /api/v1/auth/me
DELETE /api/v1/auth/me
GET    /api/v1/auth/context
```

### Supabase Auth operations

```text
signUp()
signInWithPassword()
signOut()
resetPasswordForEmail()
updateUser()
refreshSession()
```

We are intentionally **not duplicating Supabase's identity/session system inside FastAPI**.

---

# 40. What Comes Immediately After Authentication

Once Authentication is designed, the next module should be:

## Organizations & Members

Because the rest of the system depends on this.

The dependency chain is:

```text
Authentication
      ↓
Organizations
      ↓
Members / Roles
      ↓
Projects
      ↓
Documents
      ↓
Processing
      ↓
Search
      ↓
RAG
      ↓
Chat
      ↓
Research Reports
      ↓
Analytics
```

For example, a document can't simply belong to a user:

```text
Document → User
```

We want:

```text
User
 ↓
Organization
 ↓
Project
 ↓
Document
```

That gives us the multi-tenant architecture we want to demonstrate.

---

# 41. Complete Design Order

We'll design the project in this exact order:

```text
PHASE A — FOUNDATION
├── Requirements
├── Architecture
├── API conventions
├── Database conventions
└── Security model

PHASE B — IDENTITY
├── Authentication
├── Organizations
├── Members
├── Roles
└── Invitations

PHASE C — KNOWLEDGE
├── Projects
├── Documents
├── File storage
├── Document processing
├── Background jobs
└── Embeddings

PHASE D — INTELLIGENCE
├── Vector search
├── Keyword search
├── Hybrid search
├── Reranking
├── RAG
├── Chat
└── Citations

PHASE E — RESEARCH
├── Document comparison
├── Research workflows
├── Report generation
└── Evidence tracking

PHASE F — PLATFORM
├── Analytics
├── Notifications
├── Audit logs
├── Rate limiting
└── Admin

PHASE G — PRODUCTION
├── Docker
├── CI/CD
├── Testing
├── Security scanning
├── Monitoring
└── Cloud deployment
```

This is now the **master blueprint**. We should not start coding until the next few modules are designed enough that we know what we're building.

The immediate next design section is **Organizations & Members**, where we'll define the organization/member database schema, role model, invitations, organization-switching flow, all endpoints, request/response fields, authorization rules, and the exact data flow from signup → organization creation → inviting a member → member accepting the invitation.

---

# Complete System Design & Implementation Blueprint

## 1. Product goal

Build a multi-tenant AI knowledge and research platform where a user can:

```text
Sign up
  ↓
Create/join organization
  ↓
Create project
  ↓
Upload documents
  ↓
Documents processed asynchronously
  ↓
Search knowledge
  ↓
Ask AI questions
  ↓
Receive cited answers
  ↓
Compare documents
  ↓
Generate research reports
  ↓
View usage / activity
```

The application is **not just a RAG chatbot**.

RAG is one subsystem inside a larger product.

---

# 2. High-level architecture

```text
                                    USER
                                      │
                                      ▼
                             ┌─────────────────┐
                             │ Browser         │
                             │ Next.js / React │
                             └────────┬────────┘
                                      │ HTTPS
                                      ▼
                             ┌─────────────────┐
                             │ FastAPI         │
                             │ REST API        │
                             └────────┬────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
   ┌───────────────┐          ┌──────────────┐           ┌──────────────┐
   │ PostgreSQL    │          │ Redis        │           │ File Storage │
   │ + pgvector    │          │ queue/cache  │           │ PDFs/DOCX    │
   └───────┬───────┘          └──────┬───────┘           └──────────────┘
           │                          │
           │                          ▼
           │                   ┌──────────────┐
           │                   │ ARQ Worker   │
           │                   └──────┬───────┘
           │                          │
           │                          ▼
           │                 ┌──────────────────┐
           │                 │ Document / AI    │
           │                 │ Processing       │
           │                 └────────┬─────────┘
           │                          │
           └──────────────┬───────────┘
                          ▼
                 ┌──────────────────┐
                 │ Search / RAG     │
                 │ Retrieval        │
                 │ Reranking        │
                 │ Prompting        │
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │ Gemini API       │
                 └──────────────────┘
```

---

# 3. Technology stack

## Frontend

```text
Next.js
React
JavaScript
Tailwind CSS
```

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

## Data

```text
PostgreSQL
pgvector
Redis
Supabase Storage
```

## AI

```text
Gemini
Embeddings
RAG
Hybrid Search
Reranking
```

## Background processing

```text
Redis
ARQ
Python workers
```

## DevOps

```text
Git
GitHub
Docker
Docker Compose
GitHub Actions
```

## Testing/security

```text
Pytest
Frontend tests
Swagger/OpenAPI
Trivy
pip-audit
npm audit
Sentry
```

---

# 4. Application modules

We will build the application in these modules:

```text
01. Authentication
02. Organizations
03. Members & Roles
04. Projects
05. Documents
06. Document Processing
07. Search
08. AI Chat
09. Research Reports
10. Document Comparison
11. Analytics
12. Notifications
13. Audit Logs
14. Admin
15. DevOps / Infrastructure
```

---

# 5. Common API conventions

Base URL:

```text
/api/v1
```

Examples:

```text
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/projects/{project_id}
```

Protected APIs:

```http
Authorization: Bearer <access_token>
```

Generic success:

```json
{
  "data": {}
}
```

Generic error:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project does not exist."
  }
}
```

List response:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

# 6. Module 1 — Authentication

## Purpose

Manage identity and sessions.

Supabase Auth handles:

```text
signup
login
logout
email verification
password reset
password update
session refresh
```

FastAPI handles:

```text
token verification
profile
application user context
protected API access
```

## Database

### `profiles`

```text
id
display_name
avatar_url
created_at
updated_at
```

## APIs

### GET `/auth/me`

Returns current authenticated user.

No request body.

---

### POST `/auth/bootstrap`

Purpose:

Create application-level profile after authentication.

Request:

```json
{
  "display_name": "Yadushree"
}
```

---

### PATCH `/auth/me`

Request:

```json
{
  "display_name": "New Name",
  "avatar_url": "https://..."
}
```

---

### DELETE `/auth/me`

Purpose:

Initiate account deletion.

This requires careful cleanup of:

```text
profile
organization memberships
documents
storage
conversations
reports
audit references
```

---

### GET `/auth/context`

Returns:

```json
{
  "data": {
    "user": {},
    "organizations": [
      {
        "id": "org_123",
        "name": "Acme",
        "role": "OWNER"
      }
    ]
  }
}
```

## Flow

```text
Signup
 ↓
Supabase Auth
 ↓
Email verification
 ↓
Login
 ↓
Access token
 ↓
FastAPI
 ↓
JWT verification
 ↓
Profile
 ↓
Organization context
```

---

# 7. Module 2 — Organizations

This makes the application multi-tenant.

## Database

### `organizations`

```text
id
name
slug
owner_id
created_at
updated_at
```

### `organization_members`

```text
id
organization_id
user_id
role
joined_at
```

### `organization_invitations`

```text
id
organization_id
email
role
token
invited_by
expires_at
accepted_at
created_at
```

## APIs

### POST `/organizations`

Create organization.

Request:

```json
{
  "name": "Acme Research"
}
```

Flow:

```text
User
 ↓
Create organization
 ↓
Create OWNER membership
 ↓
Return organization
```

---

### GET `/organizations`

Return organizations where current user is a member.

---

### GET `/organizations/{organization_id}`

Get organization details.

Authorization:

```text
user must belong to organization
```

---

### PATCH `/organizations/{organization_id}`

Request:

```json
{
  "name": "Updated Name"
}
```

Allowed:

```text
OWNER
ADMIN
```

depending on chosen permission policy.

---

### DELETE `/organizations/{organization_id}`

Owner-only destructive operation.

---

# 8. Module 3 — Members & Roles

## Roles

```text
OWNER
ADMIN
MEMBER
VIEWER
```

## APIs

### GET `/organizations/{organization_id}/members`

Return members.

---

### PATCH `/organizations/{organization_id}/members/{member_id}`

Change role.

Request:

```json
{
  "role": "MEMBER"
}
```

---

### DELETE `/organizations/{organization_id}/members/{member_id}`

Remove member.

---

### POST `/organizations/{organization_id}/invitations`

Request:

```json
{
  "email": "user@example.com",
  "role": "MEMBER"
}
```

---

### GET `/invitations/{token}`

Get invitation information.

---

### POST `/invitations/{token}/accept`

Accept invitation.

Flow:

```text
Admin invites user
 ↓
Invitation record
 ↓
Email/link
 ↓
User opens invitation
 ↓
Login/signup
 ↓
Accept
 ↓
Create organization_members row
```

---

# 9. Module 4 — Projects

A project is a knowledge workspace inside an organization.

Example:

```text
Acme
 ├── Market Research
 ├── Competitor Analysis
 └── Product Research
```

## Database

### `projects`

```text
id
organization_id
name
description
created_by
created_at
updated_at
```

## APIs

### POST `/organizations/{organization_id}/projects`

Request:

```json
{
  "name": "Competitor Analysis",
  "description": "Research on competitors"
}
```

---

### GET `/organizations/{organization_id}/projects`

Query:

```text
?page=1&page_size=20&search=competitor
```

---

### GET `/projects/{project_id}`

Return project details.

---

### PATCH `/projects/{project_id}`

Request:

```json
{
  "name": "Updated Project",
  "description": "Updated description"
}
```

---

### DELETE `/projects/{project_id}`

Soft-delete or archive.

---

### GET `/projects/{project_id}/summary`

Return:

```text
document count
conversation count
report count
recent activity
```

---

# 10. Module 5 — Documents

This is the beginning of the knowledge system.

Supported initial formats:

```text
PDF
DOCX
TXT
```

## Database

### `documents`

```text
id
project_id
uploaded_by
name
file_name
file_type
file_size
storage_path
status
page_count
created_at
updated_at
```

Status:

```text
UPLOADED
PROCESSING
READY
FAILED
DELETED
```

---

## APIs

### POST `/projects/{project_id}/documents`

Upload document.

Could use:

```http
multipart/form-data
```

Fields:

```text
file
```

Optional metadata:

```text
title
description
```

Response:

```json
{
  "data": {
    "document_id": "doc_123",
    "status": "UPLOADED"
  }
}
```

---

### GET `/projects/{project_id}/documents`

Query:

```text
?page=1
&page_size=20
&status=READY
&search=annual
```

---

### GET `/documents/{document_id}`

Get document details.

---

### DELETE `/documents/{document_id}`

Delete document.

This should eventually delete:

```text
file
document record
chunks
embeddings
related index records
```

---

### POST `/documents/{document_id}/retry`

Retry failed document processing.

---

### GET `/documents/{document_id}/status`

Return processing information:

```json
{
  "status": "PROCESSING",
  "progress": 72,
  "current_step": "EMBEDDING"
}
```

---

# 11. Module 6 — Document Processing

This should NOT happen inside the normal API request.

## Flow

```text
Upload
 ↓
Storage
 ↓
documents row
 ↓
Create job
 ↓
Redis queue
 ↓
Worker
 ↓
Extract text
 ↓
Normalize text
 ↓
Split into chunks
 ↓
Generate embeddings
 ↓
Store chunks + vectors
 ↓
READY
```

---

# 12. Document processing database

### `document_jobs`

```text
id
document_id
job_type
status
attempts
error_message
started_at
completed_at
created_at
```

Status:

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

---

# 13. Worker jobs

Initial job types:

```text
PROCESS_DOCUMENT
RETRY_DOCUMENT
DELETE_DOCUMENT_DATA
GENERATE_REPORT
```

Later:

```text
REINDEX_DOCUMENT
REGENERATE_EMBEDDINGS
```

---

# 14. Text extraction

For PDF:

```text
PyMuPDF
```

For DOCX:

```text
python-docx
```

The worker produces:

```text
document
 ├── page 1 text
 ├── page 2 text
 ├── page 3 text
 └── ...
```

We want page information retained because citations need it.

---

# 15. Chunking

Text becomes smaller searchable units.

Example:

```text
Document
 ↓
Page
 ↓
Paragraphs
 ↓
Chunks
```

Each chunk should keep metadata:

```text
document_id
page_number
chunk_index
text
```

---

# 16. `document_chunks` table

```text
id
document_id
chunk_index
content
page_number
token_count
embedding
created_at
```

`embedding` is the vector.

---

# 17. Embedding pipeline

```text
Chunk text
 ↓
Embedding model
 ↓
Vector
 ↓
Store in pgvector
```

Example conceptually:

```text
"Company revenue increased by 20%"
                 ↓
       [0.012, -0.31, ...]
```

The vector represents semantic meaning.

---

# 18. Module 7 — Search

We will implement search in stages.

## Stage 1

Vector search.

## Stage 2

Keyword search.

## Stage 3

Hybrid search.

## Stage 4

Reranking.

---

# 19. Search API

### POST `/projects/{project_id}/search`

Request:

```json
{
  "query": "What were the main revenue risks?",
  "limit": 10,
  "filters": {
    "document_ids": [],
    "date_from": null,
    "date_to": null
  }
}
```

Response:

```json
{
  "data": [
    {
      "chunk_id": "chunk_1",
      "document_id": "doc_1",
      "document_name": "annual-report.pdf",
      "page_number": 42,
      "content": "...",
      "score": 0.91
    }
  ]
}
```

---

# 20. Vector search flow

```text
User query
 ↓
Embedding
 ↓
pgvector similarity search
 ↓
Top K chunks
 ↓
Return results
```

---

# 21. Hybrid search flow

```text
                Query
                  │
           ┌──────┴───────┐
           ▼              ▼
     Keyword search   Vector search
           │              │
           └──────┬───────┘
                  ▼
             Merge scores
                  ↓
               Rerank
                  ↓
             Top results
```

This is more robust than vector-only search.

---

# 22. Filters

Search may later support:

```text
document
document type
date
author
project
page
tags
```

---

# 23. Module 8 — AI Chat

This is the core RAG experience.

## Database

### `conversations`

```text
id
project_id
user_id
title
created_at
updated_at
```

### `messages`

```text
id
conversation_id
role
content
created_at
```

Roles:

```text
USER
ASSISTANT
SYSTEM
```

### `message_sources`

```text
id
message_id
document_id
chunk_id
page_number
relevance_score
```

This lets us show citations.

---

# 24. Conversation APIs

### POST `/projects/{project_id}/conversations`

Request:

```json
{
  "title": "Competitor research"
}
```

---

### GET `/projects/{project_id}/conversations`

Return user's conversations.

---

### GET `/conversations/{conversation_id}`

Return conversation + messages.

---

### DELETE `/conversations/{conversation_id}`

Delete conversation.

---

# 25. Send message API

### POST `/conversations/{conversation_id}/messages`

Request:

```json
{
  "content": "What were the biggest risks mentioned in the report?"
}
```

Flow:

```text
User question
 ↓
Authenticate user
 ↓
Check project access
 ↓
Load recent conversation context
 ↓
Search project knowledge
 ↓
Retrieve top chunks
 ↓
Rerank
 ↓
Build prompt
 ↓
Send context + question to Gemini
 ↓
Generate answer
 ↓
Store assistant message
 ↓
Store source references
 ↓
Return answer + citations
```

---

# 26. Chat response

```json
{
  "data": {
    "message": {
      "id": "msg_123",
      "role": "ASSISTANT",
      "content": "The report identifies..."
    },
    "sources": [
      {
        "document_id": "doc_1",
        "document_name": "annual-report.pdf",
        "page_number": 42,
        "snippet": "..."
      }
    ]
  }
}
```

---

# 27. RAG architecture

```text
                         USER QUESTION
                               │
                               ▼
                       Query preprocessing
                               │
                               ▼
                        Query embedding
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
         Keyword search                Vector search
                │                             │
                └──────────────┬──────────────┘
                               ▼
                           Reranker
                               ▼
                        Top N chunks
                               ▼
                      Context builder
                               ▼
                       Prompt builder
                               ▼
                           Gemini
                               ▼
                          AI answer
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
            Message DB                    Citations
```

---

# 28. Prompt building

We should have a dedicated service.

Conceptually:

```text
System instructions
+
project context
+
conversation context
+
retrieved evidence
+
user question
```

The LLM should be explicitly instructed:

```text
Answer using the provided evidence.
Do not invent unsupported facts.
Cite evidence when available.
```

---

# 29. RAG safeguards

We want to reduce hallucination by:

```text
retrieval
source tracking
citation mapping
context limits
clear system instructions
evaluation
```

We should also return:

```text
"I don't have enough information in the project documents."
```

when retrieval is insufficient rather than forcing an answer.

---

# 30. Streaming AI responses

Later:

```text
POST /conversations/{id}/messages
        ↓
Gemini stream
        ↓
FastAPI stream
        ↓
Next.js displays tokens progressively
```

This improves user experience.

We can first implement non-streaming and add streaming after the basic flow works.

---

# 31. Module 9 — Research Reports

This moves beyond chat.

User might request:

> "Generate a competitor analysis."

## Database

### `research_reports`

```text
id
project_id
created_by
title
report_type
status
content
created_at
updated_at
```

Status:

```text
QUEUED
GENERATING
READY
FAILED
```

---

# 32. Report APIs

### POST `/projects/{project_id}/reports`

Request:

```json
{
  "title": "Competitor Analysis",
  "report_type": "COMPETITOR_ANALYSIS",
  "instructions": "Compare pricing and positioning."
}
```

Response:

```json
{
  "data": {
    "report_id": "report_123",
    "status": "QUEUED"
  }
}
```

Because this may take time, it should become a background job.

---

### GET `/reports/{report_id}`

Return status/content.

---

### POST `/reports/{report_id}/regenerate`

Create another generation attempt.

---

### DELETE `/reports/{report_id}`

Delete report.

---

# 33. Report generation flow

```text
User requests report
 ↓
FastAPI validates
 ↓
Create report row
 ↓
Create background job
 ↓
Redis
 ↓
Worker
 ↓
Break report into sections/questions
 ↓
Retrieve evidence
 ↓
Generate each section
 ↓
Collect citations
 ↓
Assemble report
 ↓
Save final report
 ↓
READY
```

---

# 34. Report types

Start with:

```text
SUMMARY
COMPETITOR_ANALYSIS
DOCUMENT_REVIEW
RISK_ANALYSIS
RESEARCH_BRIEF
```

Later:

```text
CUSTOM
```

---

# 35. Module 10 — Document Comparison

User chooses two or more documents.

Example:

```text
2025 Annual Report
vs
2026 Annual Report
```

## API

### POST `/projects/{project_id}/comparisons`

Request:

```json
{
  "document_ids": [
    "doc_2025",
    "doc_2026"
  ],
  "instructions": "Compare financial risks."
}
```

Response:

```json
{
  "data": {
    "comparison_id": "cmp_123",
    "status": "PROCESSING"
  }
}
```

Then worker:

```text
Documents
 ↓
Relevant sections
 ↓
Retrieval
 ↓
LLM comparison
 ↓
Citations
 ↓
Comparison result
```

---

# 36. Comparison output

```text
Topic
2025
2026
Change
Evidence
```

Example:

```text
Revenue
₹100Cr
₹120Cr
+20%
Source: annual-report.pdf p42
```

---

# 37. Module 11 — Analytics

Analytics should measure usage, not just look pretty.

## Metrics

```text
documents uploaded
documents processed
processing failures
questions asked
reports generated
active users
searches
average response latency
AI usage
```

The initial analytics endpoint counts project-linked document uploads,
completed research reports, and distinct users with recorded upload, report, or
comparison activity. Processing outcomes, processing failures, questions,
searches, response latency, and AI usage remain unavailable until the product
persists the required telemetry; the dashboard labels these metrics as not
tracked instead of showing zero.

## APIs

### GET `/organizations/{organization_id}/analytics`

Query:

```text
date_from
date_to
```

Response:

```json
{
  "data": {
    "documents_uploaded": 120,
    "questions_asked": 850,
    "reports_generated": 34,
    "active_users": 18
  }
}
```

---

# 38. Module 12 — Notifications

Examples:

```text
Document processing completed
Document processing failed
Research report ready
Invitation received
```

## Database

### `notifications`

```text
id
user_id
type
title
message
read_at
created_at
```

## APIs

### GET `/notifications`

### PATCH `/notifications/{notification_id}/read`

### PATCH `/notifications/{notification_id}/unread`

The in-app inbox and API are implemented for document processing completion,
research report completion/failure, and organization invitations. Notifications
are authenticated and recipient-scoped; the current implementation does not
send email or push notifications.
