from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.embedding_service import generate_query_embedding

def search_similar_chunks(db: Session, query: str, user_id: str, top_k: int = 5) -> list[dict]:
    """
    Search for the most relevant document chunks using vector similarity.

    Args:
        db: Database session.
        query: The user's search query.
        user_id: The authenticated user's ID (only search their documents).
        top_k: Number of top results to return.

    Returns:
        A list of dicts with chunk text, document filename, and similarity score.
    """
    query_embedding = generate_query_embedding(query)

    # Use pgvector's cosine distance operator (<=>)
    # Filter by user_id so users only see their own documents
    result = db.execute(
        sql_text("""
            SELECT
                dc.id,
                dc.text_content,
                dc.document_id,
                d.filename,
                dc.embedding <=> :embedding AS distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.user_id = :user_id
            ORDER BY dc.embedding <=> :embedding
            LIMIT :top_k
        """),
        {
            "embedding": str(query_embedding),
            "user_id": user_id,
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
