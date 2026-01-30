"""Household tasks API endpoints."""

from datetime import date
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import HouseholdTaskTable
from app.models.project import HouseholdTask
from app.models.base import Priority, RecurrencePattern, TimeSlotPreference

router = APIRouter()


@router.get("/", response_model=list[HouseholdTask])
async def list_tasks(
    active_only: bool = Query(True, description="Only return active tasks"),
    due_only: bool = Query(False, description="Only return tasks that are due"),
    db: Session = Depends(get_db),
):
    """List all household tasks."""
    query = db.query(HouseholdTaskTable)
    if active_only:
        query = query.filter(HouseholdTaskTable.is_active == True)
    if due_only:
        today = date.today()
        query = query.filter(
            (HouseholdTaskTable.next_due <= today) | (HouseholdTaskTable.next_due == None)
        )
    tasks = query.order_by(HouseholdTaskTable.name).all()
    return [_table_to_model(t) for t in tasks]


@router.get("/{task_id}", response_model=HouseholdTask)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific household task by ID."""
    task = db.query(HouseholdTaskTable).filter(HouseholdTaskTable.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _table_to_model(task)


@router.post("/", response_model=HouseholdTask, status_code=201)
async def create_task(
    name: str,
    estimated_duration_minutes: int = 60,
    recurrence: RecurrencePattern = RecurrencePattern.WEEKLY,
    priority: Priority = Priority.MEDIUM,
    preferred_days: list[int] = [],
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new household task."""
    db_task = HouseholdTaskTable(
        id=str(uuid4()),
        name=name,
        description=description,
        estimated_duration_minutes=estimated_duration_minutes,
        recurrence=recurrence.value,
        priority=priority.value,
        preferred_days=preferred_days,
        preferred_time_slots=[TimeSlotPreference.ANY.value],
        source_adapter="manual",
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return _table_to_model(db_task)


@router.post("/{task_id}/complete", response_model=HouseholdTask)
async def complete_task(task_id: str, db: Session = Depends(get_db)):
    """Mark a household task as completed and calculate next due date."""
    db_task = db.query(HouseholdTaskTable).filter(HouseholdTaskTable.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update last completed
    db_task.last_completed = date.today()

    # Calculate next due
    task_model = _table_to_model(db_task)
    db_task.next_due = task_model.calculate_next_due()

    db.commit()
    db.refresh(db_task)
    return _table_to_model(db_task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a household task."""
    db_task = db.query(HouseholdTaskTable).filter(HouseholdTaskTable.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()


def _table_to_model(table: HouseholdTaskTable) -> HouseholdTask:
    """Convert database table to Pydantic model."""
    return HouseholdTask(
        id=table.id,
        name=table.name,
        description=table.description,
        estimated_duration_minutes=table.estimated_duration_minutes,
        recurrence=RecurrencePattern(table.recurrence),
        recurrence_config=table.recurrence_config,
        last_completed=table.last_completed.date() if table.last_completed else None,
        next_due=table.next_due.date() if table.next_due else None,
        priority=Priority(table.priority),
        preferred_days=table.preferred_days or [],
        preferred_time_slots=[TimeSlotPreference(s) for s in (table.preferred_time_slots or [])],
        is_active=table.is_active,
        source_adapter=table.source_adapter,
        source_id=table.source_id,
        last_synced=table.last_synced,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
