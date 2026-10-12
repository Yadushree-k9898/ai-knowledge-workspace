import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """
    Use Gemini to generate an answer based on the retrieved context chunks.

    Args:
        query: The user's question.
        context_chunks: List of dicts with 'text' and 'filename' from retrieval.

    Returns:
        The AI-generated answer string.
    """
    if not context_chunks:
        return "I don't have enough information in your knowledge base to answer this question. Try uploading relevant documents first."

    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(f"[Source {i}: {chunk['filename']}]\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful AI assistant that answers questions based ONLY on the provided knowledge base context.
If the answer cannot be found in the context, say so honestly. Do not make up information.
Always cite which source document(s) your answer comes from.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION: {query}

Provide a clear, well-structured answer based on the context above."""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text
