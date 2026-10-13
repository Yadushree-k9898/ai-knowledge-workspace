# Project chat

### `POST /api/v1/projects/{project_id}/chat/ask`

Ask a question using only documents linked to the specified project. The
authenticated user must be a member of the project's organization. The endpoint
is limited to 20 requests per user and IP per minute.

Request:

```json
{
  "query": "What are the market growth projections?"
}
```

`query` must contain 1–4000 non-whitespace characters.

Response:

```json
{
  "data": {
    "answer": "The answer grounded in project documents...",
    "sources": [
      {
        "chunk_id": 42,
        "filename": "market-research.pdf",
        "text_preview": "Relevant passage from the document...",
        "document_id": 17
      }
    ]
  }
}
```

The original user-scoped `POST /api/v1/chat/ask` endpoint remains available
for compatibility. New project experiences should use the project-scoped
endpoint.

## Shared project conversations

Project conversations are visible to all members of the project's organization.
Every endpoint checks project membership; conversation IDs are also scoped to
the project in the URL.

* `GET /api/v1/projects/{project_id}/conversations` lists conversations, most
  recently active first.
* `POST /api/v1/projects/{project_id}/conversations` starts a conversation and
  submits its first question.
* `GET /api/v1/projects/{project_id}/conversations/{conversation_id}` returns
  the full thread and its saved citations.
* `POST /api/v1/projects/{project_id}/conversations/{conversation_id}/messages`
  asks a follow-up in an existing conversation.

Create and message requests use the same `query` shape as the project chat
endpoint. They return `data.conversation` and the ordered `data.messages`.
Conversation titles are derived from the first question. Follow-up answers use
the ten most recent saved messages as bounded context, and retrieval remains
restricted to documents linked to the project. New messages are saved only
after retrieval and answer generation succeed.

Create and follow-up requests are each limited to 20 per user and IP per minute.