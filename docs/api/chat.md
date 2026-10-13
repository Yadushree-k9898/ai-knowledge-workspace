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