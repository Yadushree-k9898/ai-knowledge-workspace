"""Persistence helpers for project-scoped chat conversations."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation
from app.db.models.message import Message


def list_conversations(db: Session, project_id: str) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.project_id == project_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )


def get_conversation(
    db: Session,
    *,
    project_id: str,
    conversation_id: str,
    for_update: bool = False,
) -> Conversation | None:
    query = (
        db.query(Conversation)
        .filter(
            Conversation.project_id == project_id,
            Conversation.id == conversation_id,
        )
    )
    if for_update:
        query = query.with_for_update()
    return query.first()


def list_messages(db: Session, conversation_id: str) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.sequence)
        .all()
    )


def get_next_message_sequence(db: Session, conversation_id: str) -> int:
    latest = (
        db.query(func.max(Message.sequence))
        .filter(Message.conversation_id == conversation_id)
        .scalar()
    )
    return 0 if latest is None else latest + 1


def create_message(
    db: Session,
    *,
    message_id: str,
    conversation_id: str,
    sequence: int,
    user_id: str | None,
    role: str,
    content: str,
    sources: list[dict],
    created_at: datetime,
) -> Message:
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        sequence=sequence,
        user_id=user_id,
        role=role,
        content=content,
        sources=sources,
        created_at=created_at,
    )
    db.add(message)
    return message