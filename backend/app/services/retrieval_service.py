from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.embedding_service import generate_query_embedding

def search_similar_chunks(
    db: Session,
    query: str,
    user_id: str | None = None,
    top_k: int = 5,
    project_id: str | None = None,
) -> list[dict]:
    """
    Search for the most relevant document chunks using vector similarity.

    Args:
        db: Database session.
        query: The user's search query.
        user_id: The authenticated user's ID for user-scoped searches.
        top_k: Number of top results to return.
        project_id: Optional project scope, restricted to linked documents.

    Returns:
        A list of dicts with chunk text, document filename, and similarity score.
    """
    if (user_id is None) == (project_id is None):
        raise ValueError("Provide exactly one of user_id or project_id.")

    query_embedding = generate_query_embedding(query)

    if project_id is not None:
        scope_join = "JOIN project_documents pd ON pd.document_id = d.id"
        scope_filter = "pd.project_id = :project_id"
        scope_parameters = {"project_id": project_id}
    else:
        scope_join = ""
        scope_filter = "d.user_id = :user_id"
        scope_parameters = {"user_id": user_id}

    result = db.execute(
        sql_text(f"""
            SELECT
                dc.id,
                dc.text_content,
                dc.document_id,
                d.filename,
                dc.embedding <=> :embedding AS distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            {scope_join}
            WHERE {scope_filter}
            ORDER BY dc.embedding <=> :embedding
            LIMIT :top_k
        """),
        {
            "embedding": str(query_embedding),
            **scope_parameters,
            "top_k": top_k,
        },
    )

    rows = result.fetchall()
    return [
        {
            "chunk_id": row[0],
            "text": row[1],
            "document_id": row[2],
            "filename": row[3],
            "distance": row[4],
        }
        for row in rows
    ]
