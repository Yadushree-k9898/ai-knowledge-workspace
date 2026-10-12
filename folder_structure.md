# AI Knowledge & Research Workspace — Full Folder Structure

```text
ai-knowledge-workspace/
│
├── frontend/                              # Next.js frontend
│   │
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.js
│   │   ├── globals.css
│   │   │
│   │   ├── login/
│   │   │   └── page.js
│   │   │
│   │   ├── signup/
│   │   │   └── page.js
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.js
│   │   │
│   │   ├── organizations/
│   │   │   ├── page.js
│   │   │   └── [organizationId]/
│   │   │       ├── page.js
│   │   │       ├── members/
│   │   │       │   └── page.js
│   │   │       └── settings/
│   │   │           └── page.js
│   │   │
│   │   ├── projects/
│   │   │   ├── page.js
│   │   │   └── [projectId]/
│   │   │       ├── page.js
│   │   │       ├── documents/
│   │   │       │   └── page.js
│   │   │       ├── search/
│   │   │       │   └── page.js
│   │   │       ├── chat/
│   │   │       │   └── page.js
│   │   │       ├── reports/
│   │   │       │   └── page.js
│   │   │       └── comparisons/
│   │   │           └── page.js
│   │   │
│   │   ├── invitations/
│   │   │   └── [token]/
│   │   │       └── page.js
│   │   │
│   │   └── notifications/
│   │       └── page.js
│   │
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.js
│   │   │   ├── Input.js
│   │   │   ├── Modal.js
│   │   │   ├── Spinner.js
│   │   │   ├── ErrorMessage.js
│   │   │   └── EmptyState.js
│   │   │
│   │   ├── auth/
│   │   │   ├── LoginForm.js
│   │   │   ├── SignupForm.js
│   │   │   └── ProtectedRoute.js
│   │   │
│   │   ├── organizations/
│   │   │   ├── OrganizationCard.js
│   │   │   ├── MemberList.js
│   │   │   ├── InviteMemberForm.js
│   │   │   └── RoleSelector.js
│   │   │
│   │   ├── projects/
│   │   │   ├── ProjectCard.js
│   │   │   ├── ProjectForm.js
│   │   │   └── ProjectHeader.js
│   │   │
│   │   ├── documents/
│   │   │   ├── UploadDocument.js
│   │   │   ├── DocumentList.js
│   │   │   ├── DocumentCard.js
│   │   │   └── ProcessingStatus.js
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.js
│   │   │   ├── SearchFilters.js
│   │   │   └── SearchResults.js
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatWindow.js
│   │   │   ├── MessageList.js
│   │   │   ├── MessageInput.js
│   │   │   └── SourceCitation.js
│   │   │
│   │   ├── reports/
│   │   │   ├── ReportList.js
│   │   │   ├── ReportViewer.js
│   │   │   └── ReportGenerator.js
│   │   │
│   │   └── comparisons/
│   │       ├── ComparisonForm.js
│   │       └── ComparisonView.js
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useOrganization.js
│   │   ├── useProjects.js
│   │   ├── useDocuments.js
│   │   └── useChat.js
│   │
│   ├── lib/
│   │   ├── supabase.js
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── constants.js
│   │
│   ├── services/
│   │   ├── authService.js
│   │   ├── organizationService.js
│   │   ├── projectService.js
│   │   ├── documentService.js
│   │   ├── searchService.js
│   │   ├── chatService.js
│   │   ├── reportService.js
│   │   └── notificationService.js
│   │
│   ├── public/
│   │   └── ...
│   │
│   ├── .env.local
│   ├── .env.example
│   ├── .gitignore
│   ├── package.json
│   └── next.config.js
│
│
├── backend/                               # FastAPI backend
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── profile.py
│   │   │   │   ├── organization.py
│   │   │   │   ├── organization_member.py
│   │   │   │   ├── organization_invitation.py
│   │   │   │   ├── project.py
│   │   │   │   ├── document.py
│   │   │   │   ├── document_chunk.py
│   │   │   │   ├── document_job.py
│   │   │   │   ├── conversation.py
│   │   │   │   ├── message.py
│   │   │   │   ├── message_source.py
│   │   │   │   ├── research_report.py
│   │   │   │   ├── comparison.py
│   │   │   │   ├── notification.py
│   │   │   │   └── audit_log.py
│   │   │   │
│   │   │   └── migrations/
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │           └── ...
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth_middleware.py
│   │   │   ├── request_id.py
│   │   │   └── error_handler.py
│   │   │
│   │   ├── modules/
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── dependencies.py
│   │   │   │
│   │   │   ├── organizations/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── dependencies.py
│   │   │   │
│   │   │   ├── projects/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── dependencies.py
│   │   │   │
│   │   │   ├── documents/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── dependencies.py
│   │   │   │
│   │   │   ├── search/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── vector_search.py
│   │   │   │   ├── keyword_search.py
│   │   │   │   └── reranker.py
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── prompt_builder.py
│   │   │   │   └── llm.py
│   │   │   │
│   │   │   ├── reports/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── generator.py
│   │   │   │
│   │   │   ├── comparisons/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   │
│   │   │   ├── notifications/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   │
│   │   │   └── audit/
│   │   │       ├── router.py
│   │   │       ├── schemas.py
│   │   │       └── service.py
│   │   │
│   │   ├── services/
│   │   │   ├── storage_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── document_parser.py
│   │   │   ├── chunking_service.py
│   │   │   ├── retrieval_service.py
│   │   │   └── citation_service.py
│   │   │
│   │   ├── workers/
│   │   │   ├── worker.py
│   │   │   ├── queue.py
│   │   │   └── jobs/
│   │   │       ├── process_document.py
│   │   │       ├── delete_document.py
│   │   │       ├── generate_report.py
│   │   │       └── generate_comparison.py
│   │   │
│   │   └── utils/
│   │       ├── pagination.py
│   │       ├── validators.py
│   │       └── helpers.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── auth/
│   │   │   ├── test_signup.py
│   │   │   ├── test_login.py
│   │   │   └── test_profile.py
│   │   ├── organizations/
│   │   ├── projects/
│   │   ├── documents/
│   │   ├── search/
│   │   ├── chat/
│   │   └── reports/
│   │
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   └── pytest.ini
│
│
├── docs/                                  # Project documentation
│   │
│   ├── system-design/
│   │   ├── 01-overview.md
│   │   ├── 02-architecture.md
│   │   ├── 03-authentication.md
│   │   ├── 04-organizations.md
│   │   ├── 05-projects.md
│   │   ├── 06-documents.md
│   │   ├── 07-document-processing.md
│   │   ├── 08-search.md
│   │   ├── 09-rag.md
│   │   ├── 10-chat.md
│   │   ├── 11-research-reports.md
│   │   ├── 12-comparisons.md
│   │   ├── 13-analytics.md
│   │   ├── 14-security.md
│   │   └── 15-devops.md
│   │
│   ├── api/
│   │   ├── authentication.md
│   │   ├── organizations.md
│   │   ├── projects.md
│   │   ├── documents.md
│   │   ├── search.md
│   │   ├── chat.md
│   │   └── reports.md
│   │
│   └── database/
│       ├── schema.md
│       ├── relationships.md
│       └── indexes.md
│
│
├── infrastructure/
│   │
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   └── docker-compose.prod.yml
│   │
│   └── scripts/
│       ├── start.sh
│       ├── stop.sh
│       └── health-check.sh
│
│
├── .github/
│   └── workflows/
│       ├── backend-tests.yml
│       ├── frontend-tests.yml
│       ├── security.yml
│       └── deploy.yml
│
│
├── .gitignore
├── .env.example
├── README.md
├── LICENSE
└── docker-compose.yml
```

## How to think about it

The project has **4 major parts**:

```text
ai-knowledge-workspace/
│
├── frontend/          → What the user sees
│
├── backend/           → APIs + business logic + AI
│
├── docs/              → Our system-design documentation
│
└── infrastructure/    → Docker / deployment / DevOps
```

Inside the backend:

```text
backend/
│
├── modules/           → Business features
│   ├── auth
│   ├── organizations
│   ├── projects
│   ├── documents
│   ├── search
│   ├── chat
│   └── reports
│
├── services/          → Reusable technical logic
│
├── db/                → Database
│
└── workers/           → Background processing
```

### One important point

**This is the final planned structure, but we do NOT need to physically create every file on day one.**

We'll create the folders/files progressively, while keeping this as the target architecture.

The first physical structure we'll actually create is just:

```text
ai-knowledge-workspace/
├── frontend/
└── backend/
```

Then we'll build **frontend → backend → database → authentication**, and expand into the remaining modules in the order we've designed.
