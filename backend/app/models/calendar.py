"""Calendar and time block models."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import Field, computed_field

from app.models.base import BaseEntity, TaskType


class TimeBlockStatus(str, Enum):
    """Status of a scheduled time block."""

    SCHEDULED = "scheduled"  # Auto-scheduled, not yet confirmed
    CONFIRMED = "confirmed"  # User confirmed the block
    COMPLETED = "completed"  # Work done
    SKIPPED = "skipped"  # User skipped this block
    RESCHEDULED = "rescheduled"  # Moved to different time


class TimeBlock(BaseEntity):
    """A scheduled block of time for a specific task."""

    # What this block is for
    task_type: TaskType
    task_id: str  # UUID as string - reference to Project, HouseholdTask, Assignment, etc.
    task_name: str  # Denormalized for display

    # When
    start_time: datetime
    end_time: datetime

    # Calendar sync
    google_event_id: Optional[str] = None
    is_synced_to_calendar: bool = False

    # Status
    status: TimeBlockStatus = TimeBlockStatus.SCHEDULED

    # Tracking
    actual_duration_minutes: Optional[int] = None  # For completed blocks
    notes: Optional[str] = None

    @computed_field
    @property
    def duration(self) -> timedelta:
        """Calculate block duration."""
        return self.end_time - self.start_time

    @computed_field
    @property
    def duration_hours(self) -> float:
        """Duration in hours for hour tracking."""
        return self.duration.total_seconds() / 3600

    @computed_field
    @property
    def is_past(self) -> bool:
        """Check if block is in the past."""
        return self.end_time < datetime.utcnow()

    @computed_field
    @property
    def is_current(self) -> bool:
        """Check if block is currently active."""
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time


class ExternalEvent(BaseEntity):
    """An event from Google Calendar (read-only - meetings, etc.)."""

    google_event_id: str

    title: str
    description: Optional[str] = None

    start_time: datetime
    end_time: datetime

    is_all_day: bool = False
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None

    # User can classify the event
    event_category: str = Field(default="meeting", description="meeting, focus, personal, etc.")

    # Sync tracking
    calendar_id: str = Field(default="primary")
    last_synced: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def duration(self) -> timedelta:
        """Calculate event duration."""
        return self.end_time - self.start_time


class TimeBlockCreate(BaseEntity):
    """Schema for creating a time block."""

    task_type: TaskType
    task_id: str
    task_name: str
    start_time: datetime
    end_time: datetime


class TimeBlockUpdate(BaseEntity):
    """Schema for updating a time block."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[TimeBlockStatus] = None
    actual_duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class CalendarSyncResult(BaseEntity):
    """Result of a calendar sync operation."""

    events_fetched: int = 0
    events_added: int = 0
    events_updated: int = 0
    events_removed: int = 0
    blocks_created: int = 0
    blocks_synced: int = 0
    conflicts_detected: int = 0
    sync_time: datetime = Field(default_factory=datetime.utcnow)
    errors: list[str] = Field(default=[])
