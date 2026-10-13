# Project search

### `POST /api/v1/projects/{project_id}/search`

Search retrieves relevant chunks only from documents linked to the specified
project. The authenticated user must be a member of the project's organization.
Search is limited to 60 requests per user and IP per minute.

Request:

```json
{
  "query": "What are the market growth projections?",
  "limit": 10
}
```

`query` must contain 1–4000 non-whitespace characters. `limit` is optional and
defaults to 10, with a maximum of 20 results.

Response:

```json
{
  "data": [
    {
      "chunk_id": 42,
      "document_id": 17,
      "filename": "market-research.pdf",
      "text": "Relevant passage from the document...",
      "distance": 0.18
    }
  ]
}
```