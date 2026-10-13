import asyncio

import pytest

from app.modules.chat import router as chat_module
from app.modules.search import service as search_service
from app.services import retrieval_service


class FakeResult:
    def fetchall(self):
        return [(4, "Project-scoped result", 12, "research.txt", 0.12)]


class FakeDb:
    def __init__(self):
        self.statement = None
        self.parameters = None

    def execute(self, statement, parameters):
        self.statement = str(statement)
        self.parameters = parameters
        return FakeResult()


def test_retrieval_filters_by_linked_project_and_not_uploader(monkeypatch):
    db = FakeDb()
    monkeypatch.setattr(
        retrieval_service,
        "generate_query_embedding",
        lambda query: [0.25] * 768,
    )

    results = retrieval_service.search_similar_chunks(
        db,
        "market growth",
        project_id="project-7",
        top_k=3,
    )

    assert "JOIN project_documents pd ON pd.document_id = d.id" in db.statement
    assert "pd.project_id = :project_id" in db.statement
    assert "d.user_id = :user_id" not in db.statement
    assert db.parameters["project_id"] == "project-7"
    assert db.parameters["top_k"] == 3
    assert results == [
        {
            "chunk_id": 4,
            "text": "Project-scoped result",
            "document_id": 12,
            "filename": "research.txt",
            "distance": 0.12,
        }
    ]


def test_retrieval_requires_exactly_one_scope(monkeypatch):
    monkeypatch.setattr(
        retrieval_service,
        "generate_query_embedding",
        lambda query: [0.25] * 768,
    )
    with pytest.raises(ValueError, match="exactly one"):
        retrieval_service.search_similar_chunks(
            FakeDb(),
            "query",
            top_k=3,
        )


def test_project_search_checks_membership_before_retrieval(monkeypatch):
    calls = []
    monkeypatch.setattr(
        search_service.project_service,
        "get_project",
        lambda db, project_id, user_id: calls.append(("authorize", project_id, user_id)),
    )
    monkeypatch.setattr(
        search_service,
        "search_similar_chunks",
        lambda db, query, **kwargs: calls.append(("search", query, kwargs)) or [],
    )

    results = search_service.search_project_documents(
        object(),
        project_id="project-7",
        user_id="member-1",
        query="market growth",
        limit=7,
    )

    assert results == []
    assert calls == [
        ("authorize", "project-7", "member-1"),
        (
            "search",
            "market growth",
            {"top_k": 7, "project_id": "project-7"},
        ),
    ]


def test_project_chat_uses_project_retrieval_and_returns_citations(monkeypatch):
    calls = []
    chunk = {
        "chunk_id": 5,
        "document_id": 12,
        "filename": "research.txt",
        "text": "Relevant supporting text.",
    }
    monkeypatch.setattr(
        chat_module.project_service,
        "get_project",
        lambda db, project_id, user_id: calls.append(
            ("authorize", project_id, user_id)
        ),
    )
    monkeypatch.setattr(
        chat_module,
        "search_similar_chunks",
        lambda db, query, **kwargs: calls.append(
            ("retrieve", query, kwargs)
        ) or [chunk],
    )
    monkeypatch.setattr(
        chat_module,
        "generate_answer",
        lambda query, sources: "Answer with a citation.",
    )

    response = asyncio.run(
        chat_module.ask_project_question(
            "project-7",
            chat_module.ProjectChatRequest(query="  market growth  "),
            db=object(),
            user={"id": "member-1"},
        )
    )

    assert calls == [
        ("authorize", "project-7", "member-1"),
        ("retrieve", "market growth", {"top_k": 5, "project_id": "project-7"}),
    ]
    assert response["data"]["answer"] == "Answer with a citation."
    assert response["data"]["sources"] == [
        {
            "chunk_id": 5,
            "filename": "research.txt",
            "text_preview": "Relevant supporting text.",
            "document_id": 12,
        }
    ]
