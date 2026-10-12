"""
Projects repository — database access layer.

All SQL queries for the Project table live here.
Business logic belongs in service.py.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.db.models.project import Project


def create_project(
    db: Session, *, project_id: str, organization_id: str, name: str, description: str | None, created_by: str
) -> Project:
    """Create a new project row."""
    project = Project(
        id=project_id,
        organization_id=organization_id,
        name=name,
        description=description,
        created_by=created_by,
    )
    db.add(project)
    db.flush()
    return project


def get_project_by_id(db: Session, project_id: str) -> Project | None:
    """Fetch a project by primary key."""
    return db.query(Project).filter(Project.id == project_id).first()


def list_projects(
    db: Session,
    organization_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> tuple[list[Project], int]:
    """
    List projects for an organization with pagination and optional search.
    Returns (projects, total_count).
    """
    query = db.query(Project).filter(Project.organization_id == organization_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            Project.name.ilike(search_pattern) | Project.description.ilike(search_pattern)
        )

    total = query.count()
    offset = (page - 1) * page_size

    projects = (
        query
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return projects, total


def update_project(
    db: Session,
    project: Project,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    """Update mutable project fields. Only provided values are changed."""
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    db.flush()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    """Hard-delete a project row."""
    db.delete(project)
    db.flush()


def count_projects_in_org(db: Session, organization_id: str) -> int:
    """Return the number of projects in an organization."""
    return db.query(Project).filter(Project.organization_id == organization_id).count()
