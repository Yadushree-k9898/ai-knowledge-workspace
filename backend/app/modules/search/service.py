from sqlalchemy.orm import Session

from app.modules.projects import service as project_service
from app.services.retrieval_service import search_similar_chunks


def search_project_documents(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    query: str,
    limit: int = 10,
) -> list[dict]:
    project_service.get_project(db, project_id, user_id)
    return search_similar_chunks(
        db,
        query,
        top_k=limit,
        project_id=project_id,
    )