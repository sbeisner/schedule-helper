"""Calendar API endpoints for time blocks and external events."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import TimeBlockTable, ExternalEventTable
from app.models.calendar import (
    TimeBlock,
    TimeBlockCreate,
    TimeBlockUpdate,
    TimeBlockStatus,
    ExternalEvent,
)
from app.models.base import TaskType

router = APIRouter()


# Time Block endpoints
@router.get("/blocks", response_model=list[TimeBlock])
async def list_time_blocks(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[TimeBlockStatus] = Query(None),
    db: Session = Depends(get_db),
):
    """List time blocks within a date range."""
    query = db.query(TimeBlockTable)

    if not start_date:
        start_date = datetime.utcnow()
    if not end_date:
        end_date = start_date + timedelta(days=14)

    query = query.filter(
        TimeBlockTable.start_time >= start_date,
        TimeBlockTable.end_time <= end_date,
    )

    if status:
        query = query.filter(TimeBlockTable.status == status.value)

    blocks = query.order_by(TimeBlockTable.start_time).all()
    return [_block_to_model(b) for b in blocks]


@router.get("/blocks/{block_id}", response_model=TimeBlock)
async def get_time_block(block_id: str, db: Session = Depends(get_db)):
    """Get a specific time block."""
    block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Time block not found")
    return _block_to_model(block)


@router.post("/blocks", response_model=TimeBlock, status_code=201)
async def create_time_block(block: TimeBlockCreate, db: Session = Depends(get_db)):
    """Create a new time block."""
    db_block = TimeBlockTable(
        id=str(uuid4()),
        task_type=block.task_type.value,
        task_id=block.task_id,
        task_name=block.task_name,
        start_time=block.start_time,
        end_time=block.end_time,
        status=TimeBlockStatus.SCHEDULED.value,
    )
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return _block_to_model(db_block)


@router.put("/blocks/{block_id}", response_model=TimeBlock)
async def update_time_block(
    block_id: str, update: TimeBlockUpdate, db: Session = Depends(get_db)
):
    """Update a time block."""
    db_block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Time block not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            value = value.value
        setattr(db_block, field, value)

    db.commit()
    db.refresh(db_block)
    return _block_to_model(db_block)


@router.post("/blocks/{block_id}/complete", response_model=TimeBlock)
async def complete_time_block(
    block_id: str,
    actual_minutes: Optional[int] = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Mark a time block as completed."""
    db_block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Time block not found")

    db_block.status = TimeBlockStatus.COMPLETED.value
    if actual_minutes:
        db_block.actual_duration_minutes = actual_minutes
    if notes:
        db_block.notes = notes

    db.commit()
    db.refresh(db_block)
    return _block_to_model(db_block)


@router.post("/blocks/{block_id}/skip", response_model=TimeBlock)
async def skip_time_block(
    block_id: str,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Mark a time block as skipped."""
    db_block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Time block not found")

    db_block.status = TimeBlockStatus.SKIPPED.value
    if notes:
        db_block.notes = notes

    db.commit()
    db.refresh(db_block)
    return _block_to_model(db_block)


@router.delete("/blocks/{block_id}", status_code=204)
async def delete_time_block(block_id: str, db: Session = Depends(get_db)):
    """Delete a time block."""
    db_block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Time block not found")
    db.delete(db_block)
    db.commit()


# External Event endpoints
@router.get("/events", response_model=list[ExternalEvent])
async def list_external_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """List external calendar events."""
    query = db.query(ExternalEventTable)

    if not start_date:
        start_date = datetime.utcnow()
    if not end_date:
        end_date = start_date + timedelta(days=14)

    query = query.filter(
        ExternalEventTable.start_time >= start_date,
        ExternalEventTable.end_time <= end_date,
    )

    events = query.order_by(ExternalEventTable.start_time).all()
    return [_event_to_model(e) for e in events]


def _block_to_model(table: TimeBlockTable) -> TimeBlock:
    """Convert database table to Pydantic model."""
    return TimeBlock(
        id=table.id,
        task_type=TaskType(table.task_type),
        task_id=table.task_id,
        task_name=table.task_name,
        start_time=table.start_time,
        end_time=table.end_time,
        google_event_id=table.google_event_id,
        is_synced_to_calendar=table.is_synced_to_calendar,
        status=TimeBlockStatus(table.status),
        actual_duration_minutes=table.actual_duration_minutes,
        notes=table.notes,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


def _event_to_model(table: ExternalEventTable) -> ExternalEvent:
    """Convert database table to Pydantic model."""
    return ExternalEvent(
        id=table.id,
        google_event_id=table.google_event_id,
        title=table.title,
        description=table.description,
        start_time=table.start_time,
        end_time=table.end_time,
        is_all_day=table.is_all_day,
        is_recurring=table.is_recurring,
        recurrence_rule=table.recurrence_rule,
        event_category=table.event_category,
        calendar_id=table.calendar_id,
        last_synced=table.last_synced,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
