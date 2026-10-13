from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.projects import service as project_service
from app.modules.chat import conversation_service
from app.modules.chat.schemas import (
    ConversationDetailEnvelope,
    ConversationListEnvelope,
    ConversationRequest,
)
from app.services.retrieval_service import search_similar_chunks
from app.services.chat_service import generate_answer

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])
project_chat_router = APIRouter(prefix="/api/v1/projects", tags=["Project Chat"])

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


class ProjectChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty.")
        return value


class ProjectChatResponse(BaseModel):
    data: ChatResponse


@project_chat_router.get(
    "/{project_id}/conversations",
    response_model=ConversationListEnvelope,
)
async def list_project_conversations(
    project_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    conversations = conversation_service.list_project_conversations(
        db,
        project_id=project_id,
        user_id=user["id"],
    )
    return {"data": conversations}


@project_chat_router.get(
    "/{project_id}/conversations/{conversation_id}",
    response_model=ConversationDetailEnvelope,
)
async def get_project_conversation(
    project_id: str,
    conversation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    conversation = conversation_service.get_project_conversation(
        db,
        project_id=project_id,
        conversation_id=conversation_id,
        user_id=user["id"],
    )
    return {"data": conversation}


@project_chat_router.post(
    "/{project_id}/conversations",
    response_model=ConversationDetailEnvelope,
    dependencies=[Depends(rate_limit("project-conversation-create", limit=20, window_seconds=60))],
)
async def create_project_conversation(
    project_id: str,
    request: ConversationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    conversation = conversation_service.ask_in_project_conversation(
        db,
        project_id=project_id,
        conversation_id=None,
        user_id=user["id"],
        query=request.query,
    )
    return {"data": conversation}


@project_chat_router.post(
    "/{project_id}/conversations/{conversation_id}/messages",
    response_model=ConversationDetailEnvelope,
    dependencies=[Depends(rate_limit("project-conversation-message", limit=20, window_seconds=60))],
)
async def add_project_conversation_message(
    project_id: str,
    conversation_id: str,
    request: ConversationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    conversation = conversation_service.ask_in_project_conversation(
        db,
        project_id=project_id,
        conversation_id=conversation_id,
        user_id=user["id"],
        query=request.query,
    )
    return {"data": conversation}


@project_chat_router.post(
    "/{project_id}/chat/ask",
    response_model=ProjectChatResponse,
    dependencies=[Depends(rate_limit("project-chat", limit=20, window_seconds=60))],
)
async def ask_project_question(
    project_id: str,
    request: ProjectChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    project_service.get_project(db, project_id, user["id"])
    relevant_chunks = search_similar_chunks(
        db,
        request.query,
        top_k=5,
        project_id=project_id,
    )
    answer = generate_answer(request.query, relevant_chunks)
    sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "filename": chunk["filename"],
            "text_preview": (
                chunk["text"][:200] + "..."
                if len(chunk["text"]) > 200
                else chunk["text"]
            ),
            "document_id": chunk["document_id"],
        }
        for chunk in relevant_chunks
    ]
    return {"data": {"answer": answer, "sources": sources}}


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
