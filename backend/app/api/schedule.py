"""Scheduling API endpoints for generating and managing schedules."""

from datetime import datetime, date, timedelta
from typing import Optional

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

    # Generate basic schedule (placeholder - will be replaced with full algorithm)
    blocks = []

    # Simple allocation: distribute work across available days
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()

        # Check if it's a working day (M-F by default)
        is_working = day_of_week < 5

        if is_working:
            # Allocate project time in the morning (9am-12pm)
            for project in projects[:3]:  # Top 3 projects for now
                if project.hours_used < project.total_hours_allocated:
                    block = TimeBlock(
                        task_type=TaskType.PROJECT,
                        task_id=str(project.id),
                        task_name=project.name,
                        start_time=datetime.combine(current_date, datetime.min.time().replace(hour=9)),
                        end_time=datetime.combine(current_date, datetime.min.time().replace(hour=11)),
                        status=TimeBlockStatus.SCHEDULED,
                    )
                    blocks.append(block)
                    break  # One project per morning for simplicity

            # Allocate assignment time in the afternoon (1pm-3pm) if deadlines are near
            for assignment in assignments:
                days_until_due = (assignment.due_date.date() - current_date).days
                if 0 <= days_until_due <= 7:
                    block = TimeBlock(
                        task_type=TaskType.ASSIGNMENT,
                        task_id=str(assignment.id),
                        task_name=assignment.name,
                        start_time=datetime.combine(current_date, datetime.min.time().replace(hour=13)),
                        end_time=datetime.combine(current_date, datetime.min.time().replace(hour=15)),
                        status=TimeBlockStatus.SCHEDULED,
                    )
                    blocks.append(block)
                    break

        else:  # Weekend
            # Household tasks on weekends
            for task in household_tasks[:2]:
                block = TimeBlock(
                    task_type=TaskType.HOUSEHOLD,
                    task_id=str(task.id),
                    task_name=task.name,
                    start_time=datetime.combine(current_date, datetime.min.time().replace(hour=10)),
                    end_time=datetime.combine(
                        current_date,
                        datetime.min.time().replace(
                            hour=10 + (task.estimated_duration_minutes // 60),
                            minute=task.estimated_duration_minutes % 60,
                        ),
                    ),
                    status=TimeBlockStatus.SCHEDULED,
                )
                blocks.append(block)
                break

        current_date += timedelta(days=1)

    # Save to database if not preview
    if not preview_only:
        from uuid import uuid4

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

    # Calculate available hours (8 hours per weekday)
    total_available = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Weekday
            total_available += 8
        current += timedelta(days=1)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_available_hours": total_available,
        "meeting_hours": round(meeting_hours, 2),
        "hours_by_type": {k: round(v, 2) for k, v in hours_by_type.items()},
        "total_scheduled_hours": round(sum(hours_by_type.values()), 2),
        "free_hours": round(total_available - meeting_hours - sum(hours_by_type.values()), 2),
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
