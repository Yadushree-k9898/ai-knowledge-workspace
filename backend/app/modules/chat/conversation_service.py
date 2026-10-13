"""Project authorization and orchestration for shared chat conversations."""

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound
from app.db.models.conversation import Conversation
from app.modules.chat import repository
from app.modules.projects import service as project_service
from app.services.chat_service import generate_answer
from app.services.retrieval_service import search_similar_chunks

MAX_HISTORY_MESSAGES = 10
MAX_HISTORY_CHARACTERS = 12000


def list_project_conversations(
    db: Session,
    *,
    project_id: str,
    user_id: str,
) -> list[Conversation]:
    project_service.get_project(db, project_id, user_id)
    return repository.list_conversations(db, project_id)


def get_project_conversation(
    db: Session,
    *,
    project_id: str,
    conversation_id: str,
    user_id: str,
) -> dict:
    project_service.get_project(db, project_id, user_id)
    conversation = repository.get_conversation(
        db,
        project_id=project_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise ResourceNotFound("Conversation")
    return {
        "conversation": conversation,
        "messages": repository.list_messages(db, conversation.id),
    }


def ask_in_project_conversation(
    db: Session,
    *,
    project_id: str,
    conversation_id: str | None,
    user_id: str,
    query: str,
) -> dict:
    project_service.get_project(db, project_id, user_id)

    conversation = None
    prior_messages = []
    if conversation_id is not None:
        conversation = repository.get_conversation(
            db,
            project_id=project_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise ResourceNotFound("Conversation")
        prior_messages = repository.list_messages(db, conversation.id)

    retrieval_query = _retrieval_query(query, prior_messages)
    chunks = search_similar_chunks(
        db,
        retrieval_query,
        top_k=5,
        project_id=project_id,
    )
    answer = generate_answer(query, chunks, history=_bounded_history(prior_messages))
    sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "filename": chunk["filename"],
            "text_preview": chunk["text"][:200] + "..."
            if len(chunk["text"]) > 200
            else chunk["text"],
            "document_id": chunk["document_id"],
        }
        for chunk in chunks
    ]

    if conversation is None:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            created_by=user_id,
            title=query[:200],
        )
        db.add(conversation)
    else:
        conversation = repository.get_conversation(
            db,
            project_id=project_id,
            conversation_id=conversation.id,
            for_update=True,
        )
        if conversation is None:
            raise ResourceNotFound("Conversation")

    next_sequence = repository.get_next_message_sequence(db, conversation.id)
    user_message_time = datetime.now(timezone.utc)
    repository.create_message(
        db,
        message_id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        sequence=next_sequence,
        user_id=user_id,
        role="USER",
        content=query,
        sources=[],
        created_at=user_message_time,
    )
    repository.create_message(
        db,
        message_id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        sequence=next_sequence + 1,
        user_id=None,
        role="ASSISTANT",
        content=answer,
        sources=sources,
        created_at=user_message_time + timedelta(microseconds=1),
    )
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()

    updated_conversation = repository.get_conversation(
        db,
        project_id=project_id,
        conversation_id=conversation.id,
    )
    return {
        "conversation": updated_conversation,
        "messages": repository.list_messages(db, conversation.id),
    }


def _bounded_history(messages: list) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    remaining = MAX_HISTORY_CHARACTERS
    for message in reversed(messages[-MAX_HISTORY_MESSAGES:]):
        content = message.content[-remaining:]
        history.append({"role": message.role, "content": content})
        remaining -= len(content)
        if remaining <= 0:
            break
    history.reverse()
    return history


def _retrieval_query(query: str, messages: list) -> str:
    earlier_questions = [
        message.content
        for message in messages
        if message.role == "USER"
    ][-3:]
    return "\n".join([*earlier_questions, query])[-MAX_HISTORY_CHARACTERS:]
