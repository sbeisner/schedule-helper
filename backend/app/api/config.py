"""User configuration API endpoints."""

from datetime import time
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import UserConfigTable
from app.models.config import UserConfig, UserConfigUpdate, WorkSchedule

router = APIRouter()

DEFAULT_CONFIG_ID = "default"


@router.get("/", response_model=UserConfig)
async def get_config(db: Session = Depends(get_db)):
    """Get user configuration. Creates default if none exists."""
    config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    if not config:
        # Create default configuration
        default = UserConfig.create_default()
        config = UserConfigTable(
            id=DEFAULT_CONFIG_ID,
            work_schedules=[s.model_dump() for s in default.work_schedules],
            default_work_hours_per_day=default.default_work_hours_per_day,
            min_break_between_blocks_minutes=default.min_break_between_blocks_minutes,
            preferred_block_duration_minutes=default.preferred_block_duration_minutes,
            max_daily_scheduled_hours=default.max_daily_scheduled_hours,
            meeting_buffer_before_minutes=default.meeting_buffer_before_minutes,
            meeting_buffer_after_minutes=default.meeting_buffer_after_minutes,
            google_calendar_id=default.google_calendar_id,
            auto_schedule_enabled=default.auto_schedule_enabled,
            schedule_horizon_days=default.schedule_horizon_days,
            auto_sync_interval_minutes=default.auto_sync_interval_minutes,
            timezone=default.timezone,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return _table_to_model(config)


@router.put("/", response_model=UserConfig)
async def update_config(update: UserConfigUpdate, db: Session = Depends(get_db)):
    """Update user configuration."""
    config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    if not config:
        # Create with defaults first
        await get_config(db)
        config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "work_schedules" and value:
            value = [s.model_dump() if hasattr(s, "model_dump") else s for s in value]
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return _table_to_model(config)


@router.post("/work-schedule", response_model=UserConfig)
async def update_work_schedule(
    day_of_week: int,
    start_time: str,  # HH:MM format
    end_time: str,
    is_working_day: bool = True,
    db: Session = Depends(get_db),
):
    """Update work schedule for a specific day."""
    config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    if not config:
        await get_config(db)
        config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    schedules = config.work_schedules or []

    # Find and update or add the schedule for this day
    found = False
    for i, schedule in enumerate(schedules):
        if schedule.get("day_of_week") == day_of_week:
            schedules[i] = {
                "day_of_week": day_of_week,
                "start_time": start_time,
                "end_time": end_time,
                "is_working_day": is_working_day,
            }
            found = True
            break

    if not found:
        schedules.append({
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
            "is_working_day": is_working_day,
        })

    config.work_schedules = schedules
    db.commit()
    db.refresh(config)
    return _table_to_model(config)


@router.post("/google-sheets/projects")
async def set_projects_sheet(
    spreadsheet_id: str,
    range_name: str = "Projects!A2:J",
    db: Session = Depends(get_db),
):
    """Set the Google Sheets ID for projects tracking."""
    config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    if not config:
        await get_config(db)
        config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    config.google_sheets_projects_id = spreadsheet_id
    config.google_sheets_projects_range = range_name
    db.commit()
    db.refresh(config)
    return _table_to_model(config)


@router.post("/google-sheets/household")
async def set_household_sheet(
    spreadsheet_id: str,
    range_name: str = "Household!A2:H",
    db: Session = Depends(get_db),
):
    """Set the Google Sheets ID for household tasks."""
    config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    if not config:
        await get_config(db)
        config = db.query(UserConfigTable).filter(UserConfigTable.id == DEFAULT_CONFIG_ID).first()

    config.google_sheets_household_id = spreadsheet_id
    config.google_sheets_household_range = range_name
    db.commit()
    db.refresh(config)
    return _table_to_model(config)


def _table_to_model(table: UserConfigTable) -> UserConfig:
    """Convert database table to Pydantic model."""
    work_schedules = []
    for ws in table.work_schedules or []:
        work_schedules.append(
            WorkSchedule(
                day_of_week=ws.get("day_of_week"),
                start_time=time.fromisoformat(ws.get("start_time", "08:00")),
                end_time=time.fromisoformat(ws.get("end_time", "16:00")),
                is_working_day=ws.get("is_working_day", True),
            )
        )

    return UserConfig(
        id=table.id,
        work_schedules=work_schedules,
        default_work_hours_per_day=table.default_work_hours_per_day,
        min_break_between_blocks_minutes=table.min_break_between_blocks_minutes,
        preferred_block_duration_minutes=table.preferred_block_duration_minutes,
        max_daily_scheduled_hours=table.max_daily_scheduled_hours,
        meeting_buffer_before_minutes=table.meeting_buffer_before_minutes,
        meeting_buffer_after_minutes=table.meeting_buffer_after_minutes,
        google_calendar_id=table.google_calendar_id,
        google_sheets_projects_id=table.google_sheets_projects_id,
        google_sheets_projects_range=table.google_sheets_projects_range,
        google_sheets_household_id=table.google_sheets_household_id,
        google_sheets_household_range=table.google_sheets_household_range,
        auto_schedule_enabled=table.auto_schedule_enabled,
        schedule_horizon_days=table.schedule_horizon_days,
        auto_sync_interval_minutes=table.auto_sync_interval_minutes,
        timezone=table.timezone,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
