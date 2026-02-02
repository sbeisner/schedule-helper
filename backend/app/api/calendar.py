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
    CalendarSyncResult,
)
from app.models.base import TaskType
from app.services.google.calendar_service import GoogleCalendarService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


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
    return [_block_to_model(b, db) for b in blocks]


@router.get("/blocks/{block_id}", response_model=TimeBlock)
async def get_time_block(block_id: str, db: Session = Depends(get_db)):
    """Get a specific time block."""
    block = db.query(TimeBlockTable).filter(TimeBlockTable.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Time block not found")
    return _block_to_model(block, db)


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
    return _block_to_model(db_block, db)


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
    return _block_to_model(db_block, db)


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
    return _block_to_model(db_block, db)


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
    return _block_to_model(db_block, db)


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


@router.post("/sync", response_model=CalendarSyncResult)
async def sync_calendar_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Sync events from Google Calendar to local database."""
    result = CalendarSyncResult()

    try:
        # Initialize calendar service
        calendar_service = GoogleCalendarService()

        # Get calendar ID from settings
        calendar_id = settings.google_calendar_id or 'primary'

        # Fetch events from Google Calendar
        if not start_date:
            start_date = datetime.utcnow()
        if not end_date:
            end_date = start_date + timedelta(days=14)

        google_events = calendar_service.list_events(
            calendar_id=calendar_id,
            start_date=start_date,
            end_date=end_date,
        )
        result.events_fetched = len(google_events)

        # Track existing events
        existing_event_ids = {
            e.google_event_id: e
            for e in db.query(ExternalEventTable).all()
        }

        for event_data in google_events:
            google_event_id = event_data['google_event_id']

            if google_event_id in existing_event_ids:
                # Update existing event
                existing_event = existing_event_ids[google_event_id]
                existing_event.title = event_data['title']
                existing_event.description = event_data.get('description')
                existing_event.start_time = event_data['start_time']
                existing_event.end_time = event_data['end_time']
                existing_event.is_all_day = event_data['is_all_day']
                existing_event.is_recurring = event_data['is_recurring']
                existing_event.recurrence_rule = event_data.get('recurrence_rule')
                existing_event.calendar_id = event_data['calendar_id']
                existing_event.last_synced = datetime.utcnow()
                existing_event.updated_at = datetime.utcnow()
                result.events_updated += 1
            else:
                # Create new event
                new_event = ExternalEventTable(
                    id=str(uuid4()),
                    google_event_id=google_event_id,
                    title=event_data['title'],
                    description=event_data.get('description'),
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    is_all_day=event_data['is_all_day'],
                    is_recurring=event_data['is_recurring'],
                    recurrence_rule=event_data.get('recurrence_rule'),
                    calendar_id=event_data['calendar_id'],
                    last_synced=datetime.utcnow(),
                )
                db.add(new_event)
                result.events_added += 1

        db.commit()
        result.sync_time = datetime.utcnow()

    except Exception as e:
        result.errors.append(str(e))
        raise HTTPException(status_code=500, detail=f"Calendar sync failed: {str(e)}")

    return result


def _block_to_model(table: TimeBlockTable, db: Optional[Session] = None) -> TimeBlock:
    """Convert database table to Pydantic model."""
    is_completed = None

    # For assignments, check if the underlying assignment is completed
    if table.task_type == TaskType.ASSIGNMENT.value and db:
        from app.db.tables import AssignmentTable
        assignment = db.query(AssignmentTable).filter(AssignmentTable.id == table.task_id).first()
        if assignment:
            is_completed = assignment.is_completed

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
        is_completed=is_completed,
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
