"""Scheduling API endpoints for generating and managing schedules."""

from datetime import datetime, date, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import (
    ProjectTable,
    HouseholdTaskTable,
    AssignmentTable,
    TimeBlockTable,
    ExternalEventTable,
    SchedulingRuleTable,
    UserConfigTable,
)
from app.models.calendar import TimeBlock, TimeBlockStatus
from app.models.base import TaskType
from app.services.scheduler.smart_scheduler import SmartScheduler

router = APIRouter()


@router.post("/generate", response_model=list[TimeBlock])
async def generate_schedule(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    preview_only: bool = Query(True, description="If true, don't save blocks to database"),
    db: Session = Depends(get_db),
):
    """
    Generate a schedule for the specified date range.

    This is a simplified version that will be replaced with the full
    scheduling engine in Phase 3. For now, it creates basic time blocks
    for active projects and due tasks.
    """
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=14)

    # Get user config
    config = db.query(UserConfigTable).first()
    if not config:
        raise HTTPException(status_code=400, detail="User configuration not set up")

    # Get active projects
    projects = (
        db.query(ProjectTable)
        .filter(ProjectTable.is_active == True)
        .filter(ProjectTable.hours_used < ProjectTable.total_hours_allocated)
        .all()
    )

    # Get upcoming assignments
    assignments = (
        db.query(AssignmentTable)
        .filter(AssignmentTable.is_completed == False)
        .filter(AssignmentTable.due_date <= datetime.combine(end_date, datetime.max.time()))
        .all()
    )

    # Get due household tasks
    household_tasks = (
        db.query(HouseholdTaskTable)
        .filter(HouseholdTaskTable.is_active == True)
        .all()
    )

    # Get existing external events (meetings) to avoid conflicts
    external_events = (
        db.query(ExternalEventTable)
        .filter(ExternalEventTable.start_time >= datetime.combine(start_date, datetime.min.time()))
        .filter(ExternalEventTable.end_time <= datetime.combine(end_date, datetime.max.time()))
        .all()
    )

    # Use the smart scheduler
    scheduler = SmartScheduler(config)

    blocks = scheduler.generate_schedule(
        projects=projects,
        assignments=assignments,
        household_tasks=household_tasks,
        external_events=external_events,
        start_date=start_date,
        end_date=end_date,
    )

    # Save to database if not preview
    if not preview_only:
        for block in blocks:
            db_block = TimeBlockTable(
                id=str(uuid4()),
                task_type=block.task_type.value,
                task_id=block.task_id,
                task_name=block.task_name,
                start_time=block.start_time,
                end_time=block.end_time,
                status=block.status.value,
            )
            db.add(db_block)
        db.commit()

    return blocks


@router.get("/summary")
async def get_schedule_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Get a summary of scheduled time for the date range."""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Get all blocks in range
    blocks = (
        db.query(TimeBlockTable)
        .filter(TimeBlockTable.start_time >= start_dt)
        .filter(TimeBlockTable.end_time <= end_dt)
        .all()
    )

    # Calculate totals by type
    hours_by_type = {}
    for block in blocks:
        task_type = block.task_type
        duration_hours = (block.end_time - block.start_time).total_seconds() / 3600
        hours_by_type[task_type] = hours_by_type.get(task_type, 0) + duration_hours

    # Get external events
    events = (
        db.query(ExternalEventTable)
        .filter(ExternalEventTable.start_time >= start_dt)
        .filter(ExternalEventTable.end_time <= end_dt)
        .all()
    )

    meeting_hours = sum(
        (e.end_time - e.start_time).total_seconds() / 3600 for e in events
    )

    # Calculate available hours (work + personal time)
    # Weekdays: 8 work hours + 5 evening hours (4pm-9pm) = 13 hours
    # Weekends: 12 hours (9am-9pm)
    total_available = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Weekday
            total_available += 13  # Work hours + evening
        else:  # Weekend
            total_available += 12
        current += timedelta(days=1)

    total_scheduled = sum(hours_by_type.values())
    free_hours = max(0, total_available - meeting_hours - total_scheduled)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_available_hours": total_available,
        "meeting_hours": round(meeting_hours, 2),
        "hours_by_type": {k: round(v, 2) for k, v in hours_by_type.items()},
        "total_scheduled_hours": round(total_scheduled, 2),
        "free_hours": round(free_hours, 2),
        "block_count": len(blocks),
        "event_count": len(events),
    }


@router.delete("/clear")
async def clear_scheduled_blocks(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[TimeBlockStatus] = Query(TimeBlockStatus.SCHEDULED),
    db: Session = Depends(get_db),
):
    """Clear scheduled (not completed) time blocks in the date range."""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=14)

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    query = db.query(TimeBlockTable).filter(
        TimeBlockTable.start_time >= start_dt,
        TimeBlockTable.end_time <= end_dt,
    )

    if status:
        query = query.filter(TimeBlockTable.status == status.value)

    deleted_count = query.delete()
    db.commit()

    return {"deleted_count": deleted_count}
