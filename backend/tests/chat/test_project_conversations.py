import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import PermissionDenied, ResourceNotFound
from app.db.base import Base
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.project import Project
from app.modules.chat import conversation_service
from app.modules.chat.schemas import ConversationDetailEnvelope, ConversationListEnvelope


@pytest.fixture
def conversation_db():
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Conversation.__table__,
        Message.__table__,
    ]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=tables)
    db = sessionmaker(bind=engine)()
    db.add(
        Organization(
            id="org-1",
            name="Research",
            slug="research",
            owner_id="owner-1",
        )
    )
    db.add_all(
        [
            OrganizationMember(
                id="owner-member",
                organization_id="org-1",
                user_id="owner-1",
                role=OrgRole.OWNER,
            ),
            OrganizationMember(
                id="viewer-member",
                organization_id="org-1",
                user_id="viewer-1",
                role=OrgRole.VIEWER,
            ),
        ]
    )
    db.add_all(
        [
            Project(
                id="project-1",
                organization_id="org-1",
                name="Project One",
                created_by="owner-1",
            ),
            Project(
                id="project-2",
                organization_id="org-1",
                name="Project Two",
                created_by="owner-1",
            ),
        ]
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_conversation_creates_and_appends_shared_messages(
    conversation_db,
    monkeypatch,
):
    histories = []
    monkeypatch.setattr(
        conversation_service,
        "search_similar_chunks",
        lambda db, query, **kwargs: [
            {
                "chunk_id": 5,
                "document_id": 12,
                "filename": "research.txt",
                "text": f"Evidence for {query}.",
            }
        ],
    )

    def generate(query, chunks, history=None):
        histories.append(history)
        return f"Answer to {query}."

    monkeypatch.setattr(conversation_service, "generate_answer", generate)

    first = conversation_service.ask_in_project_conversation(
        conversation_db,
        project_id="project-1",
        conversation_id=None,
        user_id="owner-1",
        query="What is the market size?",
    )
    conversation_id = first["conversation"].id

    second = conversation_service.ask_in_project_conversation(
        conversation_db,
        project_id="project-1",
        conversation_id=conversation_id,
        user_id="owner-1",
        query="What supports that?",
    )

    assert second["conversation"].title == "What is the market size?"
    assert len(second["messages"]) == 4
    assert [message.role for message in second["messages"]] == [
        "USER",
        "ASSISTANT",
        "USER",
        "ASSISTANT",
    ]
    assert [message.sequence for message in second["messages"]] == [0, 1, 2, 3]
    assert second["messages"][1].sources == [
        {
            "chunk_id": 5,
            "filename": "research.txt",
            "text_preview": "Evidence for What is the market size?.",
            "document_id": 12,
        }
    ]
    assert histories == [
        [],
        [
            {"role": "USER", "content": "What is the market size?"},
            {"role": "ASSISTANT", "content": "Answer to What is the market size?."},
        ],
    ]
    ConversationDetailEnvelope.model_validate({"data": second})
    ConversationListEnvelope.model_validate({
        "data": conversation_service.list_project_conversations(
            conversation_db,
            project_id="project-1",
            user_id="viewer-1",
        )
    })

    shared = conversation_service.get_project_conversation(
        conversation_db,
        project_id="project-1",
        conversation_id=conversation_id,
        user_id="viewer-1",
    )
    assert shared["conversation"].id == conversation_id
    assert len(shared["messages"]) == 4


def test_project_membership_is_required_to_access_shared_conversations(
    conversation_db,
):
    with pytest.raises(PermissionDenied):
        conversation_service.list_project_conversations(
            conversation_db,
            project_id="project-1",
            user_id="outsider",
        )


def test_conversation_id_is_scoped_to_the_requested_project(conversation_db):
    conversation = Conversation(
        id="conversation-project-2",
        project_id="project-2",
        created_by="owner-1",
        title="Private project two data",
    )
    conversation_db.add(conversation)
    conversation_db.commit()

    with pytest.raises(ResourceNotFound):
        conversation_service.get_project_conversation(
            conversation_db,
            project_id="project-1",
            conversation_id=conversation.id,
            user_id="owner-1",
        )


def test_failed_generation_does_not_create_a_conversation(
    conversation_db,
    monkeypatch,
):
    monkeypatch.setattr(
        conversation_service,
        "search_similar_chunks",
        lambda db, query, **kwargs: [],
    )

    def fail_generation(*_args, **_kwargs):
        raise RuntimeError("AI provider unavailable")

    monkeypatch.setattr(conversation_service, "generate_answer", fail_generation)

    with pytest.raises(RuntimeError, match="AI provider unavailable"):
        conversation_service.ask_in_project_conversation(
            conversation_db,
            project_id="project-1",
            conversation_id=None,
            user_id="owner-1",
            query="Question",
        )

    assert conversation_db.query(Conversation).count() == 0
    assert conversation_db.query(Message).count() == 0
