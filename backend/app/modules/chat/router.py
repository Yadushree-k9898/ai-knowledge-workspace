from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.services.retrieval_service import search_similar_chunks
from app.services.chat_service import generate_answer

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Ask a question against your uploaded knowledge base.
    Retrieves relevant document chunks and generates an AI-powered answer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: Retrieve relevant chunks via vector similarity search
    relevant_chunks = search_similar_chunks(db, request.query, user["id"], top_k=5)

    # Step 2: Generate answer using Gemini with the retrieved context
    answer = generate_answer(request.query, relevant_chunks)

    # Step 3: Return the answer with source citations
    sources = [
        {
            "filename": chunk["filename"],
            "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
            "document_id": chunk["document_id"],
        }
        for chunk in relevant_chunks
    ]

    return ChatResponse(answer=answer, sources=sources)
