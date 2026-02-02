"""SQLAlchemy table definitions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.base import Priority, RecurrencePattern, TaskType, TimeSlotPreference
from app.models.calendar import TimeBlockStatus


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class ProjectTable(Base):
    """SQLAlchemy model for projects."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    total_hours_allocated: Mapped[float] = mapped_column(Float, default=0)
    hours_used: Mapped[float] = mapped_column(Float, default=0)
    allocation_percentage: Mapped[float] = mapped_column(Float, default=100.0)
    weekly_hour_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_hour_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    priority: Mapped[str] = mapped_column(String(20), default=Priority.MEDIUM.value)
    preferred_time_slots: Mapped[str] = mapped_column(JSON, default=list)
    min_block_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    max_block_duration_minutes: Mapped[int] = mapped_column(Integer, default=120)

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    source_adapter: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HouseholdTaskTable(Base):
    """SQLAlchemy model for household tasks."""

    __tablename__ = "household_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    recurrence: Mapped[str] = mapped_column(String(20), default=RecurrencePattern.WEEKLY.value)
    recurrence_config: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    last_completed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_due: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    priority: Mapped[str] = mapped_column(String(20), default=Priority.MEDIUM.value)
    preferred_days: Mapped[str] = mapped_column(JSON, default=list)
    preferred_time_slots: Mapped[str] = mapped_column(JSON, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    source_adapter: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CourseTable(Base):
    """SQLAlchemy model for courses."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM format
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    semester_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    semester_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    excluded_dates: Mapped[str] = mapped_column(JSON, default=list)

    syllabus_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    moodle_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    source_adapter: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AssignmentTable(Base):
    """SQLAlchemy model for assignments."""

    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hours_logged: Mapped[float] = mapped_column(Float, default=0)

    priority: Mapped[str] = mapped_column(String(20), default=Priority.HIGH.value)
    preferred_time_slots: Mapped[str] = mapped_column(JSON, default=list)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimeBlockTable(Base):
    """SQLAlchemy model for scheduled time blocks."""

    __tablename__ = "time_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    google_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_synced_to_calendar: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(20), default=TimeBlockStatus.SCHEDULED.value)
    actual_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExternalEventTable(Base):
    """SQLAlchemy model for external calendar events."""

    __tablename__ = "external_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    google_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    event_category: Mapped[str] = mapped_column(String(50), default="meeting")
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary")

    last_synced: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SchedulingRuleTable(Base):
    """SQLAlchemy model for scheduling rules."""

    __tablename__ = "scheduling_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    conditions: Mapped[str] = mapped_column(JSON, default=list)
    actions: Mapped[str] = mapped_column(JSON, default=list)

    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserConfigTable(Base):
    """SQLAlchemy model for user configuration (single row)."""

    __tablename__ = "user_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    work_schedules: Mapped[str] = mapped_column(JSON, default=list)
    default_work_hours_per_day: Mapped[float] = mapped_column(Float, default=8.0)

    min_break_between_blocks_minutes: Mapped[int] = mapped_column(Integer, default=15)
    preferred_block_duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    max_daily_scheduled_hours: Mapped[float] = mapped_column(Float, default=10.0)

    meeting_buffer_before_minutes: Mapped[int] = mapped_column(Integer, default=10)
    meeting_buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=5)

    google_calendar_id: Mapped[str] = mapped_column(String(255), default="primary")
    google_sheets_projects_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sheets_projects_range: Mapped[str] = mapped_column(String(100), default="Projects!A2:J")
    google_sheets_household_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sheets_household_range: Mapped[str] = mapped_column(String(100), default="Household!A2:H")

    auto_schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_horizon_days: Mapped[int] = mapped_column(Integer, default=14)
    auto_sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)

    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
