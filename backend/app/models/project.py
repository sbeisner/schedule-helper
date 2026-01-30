"""Project and household task models."""

from datetime import date, timedelta
from typing import Optional

from pydantic import Field, computed_field

from app.models.base import (
    BaseEntity,
    Priority,
    RecurrencePattern,
    SourceTracking,
    TimeSlotPreference,
)


class Project(BaseEntity, SourceTracking):
    """A work project with hour allocations and optional caps."""

    name: str
    description: Optional[str] = None

    # Hour tracking
    total_hours_allocated: float = Field(ge=0, description="Total hours budgeted for project")
    hours_used: float = Field(default=0, ge=0, description="Hours already logged")

    # Constraints
    weekly_hour_cap: Optional[float] = Field(
        default=None, ge=0, description="Max hours per week on this project"
    )
    daily_hour_cap: Optional[float] = Field(
        default=None, ge=0, description="Max hours per day on this project"
    )

    # Scheduling preferences
    priority: Priority = Priority.MEDIUM
    preferred_time_slots: list[TimeSlotPreference] = Field(default=[TimeSlotPreference.ANY])
    min_block_duration_minutes: int = Field(default=30, ge=15)
    max_block_duration_minutes: int = Field(default=120, le=480)

    # Timeline
    start_date: Optional[date] = None
    end_date: Optional[date] = None  # Deadline or project end
    is_active: bool = True

    @computed_field
    @property
    def hours_remaining(self) -> float:
        """Calculate remaining hours on the project."""
        return max(0, self.total_hours_allocated - self.hours_used)

    @computed_field
    @property
    def min_block_duration(self) -> timedelta:
        return timedelta(minutes=self.min_block_duration_minutes)

    @computed_field
    @property
    def max_block_duration(self) -> timedelta:
        return timedelta(minutes=self.max_block_duration_minutes)


class HouseholdTask(BaseEntity, SourceTracking):
    """A recurring household task with cadence."""

    name: str
    description: Optional[str] = None

    # Time requirements
    estimated_duration_minutes: int = Field(
        default=60, ge=5, description="How long task typically takes"
    )

    # Recurrence
    recurrence: RecurrencePattern = RecurrencePattern.WEEKLY
    recurrence_config: Optional[dict] = None  # Extra config for CUSTOM pattern
    last_completed: Optional[date] = None
    next_due: Optional[date] = None

    # Scheduling preferences
    priority: Priority = Priority.MEDIUM
    preferred_days: list[int] = Field(
        default=[], description="Preferred days of week (0=Monday, 6=Sunday)"
    )
    preferred_time_slots: list[TimeSlotPreference] = Field(default=[TimeSlotPreference.ANY])

    is_active: bool = True

    @computed_field
    @property
    def estimated_duration(self) -> timedelta:
        return timedelta(minutes=self.estimated_duration_minutes)

    def calculate_next_due(self) -> Optional[date]:
        """Calculate next due date based on recurrence pattern."""
        if not self.last_completed:
            return date.today()

        match self.recurrence:
            case RecurrencePattern.NONE:
                return None
            case RecurrencePattern.DAILY:
                return self.last_completed + timedelta(days=1)
            case RecurrencePattern.WEEKLY:
                return self.last_completed + timedelta(weeks=1)
            case RecurrencePattern.BIWEEKLY:
                return self.last_completed + timedelta(weeks=2)
            case RecurrencePattern.MONTHLY:
                # Approximate - add 30 days
                return self.last_completed + timedelta(days=30)
            case RecurrencePattern.CUSTOM:
                # Would need cron parsing here
                return self.last_completed + timedelta(weeks=1)
            case _:
                return None


class ProjectCreate(BaseEntity):
    """Schema for creating a new project."""

    name: str
    description: Optional[str] = None
    total_hours_allocated: float = Field(ge=0)
    weekly_hour_cap: Optional[float] = None
    daily_hour_cap: Optional[float] = None
    priority: Priority = Priority.MEDIUM
    preferred_time_slots: list[TimeSlotPreference] = [TimeSlotPreference.ANY]
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseEntity):
    """Schema for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None
    total_hours_allocated: Optional[float] = None
    hours_used: Optional[float] = None
    weekly_hour_cap: Optional[float] = None
    daily_hour_cap: Optional[float] = None
    priority: Optional[Priority] = None
    preferred_time_slots: Optional[list[TimeSlotPreference]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
