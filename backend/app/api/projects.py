"""Project API endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import ProjectTable
from app.models.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("/", response_model=list[Project])
async def list_projects(
    active_only: bool = Query(True, description="Only return active projects"),
    db: Session = Depends(get_db),
):
    """List all projects."""
    query = db.query(ProjectTable)
    if active_only:
        query = query.filter(ProjectTable.is_active == True)
    projects = query.order_by(ProjectTable.name).all()
    return [_table_to_model(p) for p in projects]


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    project = db.query(ProjectTable).filter(ProjectTable.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _table_to_model(project)


@router.post("/", response_model=Project, status_code=201)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    db_project = ProjectTable(
        id=str(uuid4()),
        name=project.name,
        description=project.description,
        total_hours_allocated=project.total_hours_allocated,
        allocation_percentage=project.allocation_percentage,
        weekly_hour_cap=project.weekly_hour_cap,
        daily_hour_cap=project.daily_hour_cap,
        priority=project.priority.value,
        preferred_time_slots=[s.value for s in project.preferred_time_slots],
        start_date=project.start_date,
        end_date=project.end_date,
        source_adapter="manual",
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return _table_to_model(db_project)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str, project: ProjectUpdate, db: Session = Depends(get_db)
):
    """Update a project."""
    db_project = db.query(ProjectTable).filter(ProjectTable.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "priority" and value:
            value = value.value
        elif field == "preferred_time_slots" and value:
            value = [s.value for s in value]
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return _table_to_model(db_project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project."""
    db_project = db.query(ProjectTable).filter(ProjectTable.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()


@router.post("/{project_id}/log-hours", response_model=Project)
async def log_hours(
    project_id: str,
    hours: float = Query(..., gt=0, description="Hours to log"),
    db: Session = Depends(get_db),
):
    """Log hours worked on a project."""
    db_project = db.query(ProjectTable).filter(ProjectTable.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.hours_used += hours
    db.commit()
    db.refresh(db_project)
    return _table_to_model(db_project)


def _table_to_model(table: ProjectTable) -> Project:
    """Convert database table to Pydantic model."""
    from app.models.base import Priority, TimeSlotPreference

    return Project(
        id=table.id,
        name=table.name,
        description=table.description,
        total_hours_allocated=table.total_hours_allocated,
        hours_used=table.hours_used,
        allocation_percentage=table.allocation_percentage,
        weekly_hour_cap=table.weekly_hour_cap,
        daily_hour_cap=table.daily_hour_cap,
        priority=Priority(table.priority),
        preferred_time_slots=[TimeSlotPreference(s) for s in table.preferred_time_slots],
        min_block_duration_minutes=table.min_block_duration_minutes,
        max_block_duration_minutes=table.max_block_duration_minutes,
        start_date=table.start_date.date() if table.start_date else None,
        end_date=table.end_date.date() if table.end_date else None,
        is_active=table.is_active,
        source_adapter=table.source_adapter,
        source_id=table.source_id,
        last_synced=table.last_synced,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
