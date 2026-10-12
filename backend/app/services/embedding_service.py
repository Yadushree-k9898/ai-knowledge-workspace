import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings using Gemini's embedding model.
    Returns a list of 768-dimensional vectors.
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]

def generate_query_embedding(query: str) -> list[float]:
    """
    Generate an embedding for a single search query.
    Uses 'retrieval_query' task type for better search results.
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]
