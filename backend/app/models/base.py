"""Base models and enums for Schedule Manager."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of schedulable tasks."""

    PROJECT = "project"  # Work projects with hour allocations
    COURSE = "course"  # Academic courses (fixed schedule)
    ASSIGNMENT = "assignment"  # Course assignments/deadlines
    HOUSEHOLD = "household"  # Household tasks with cadence
    PERSONAL = "personal"  # Personal tasks
    MEETING = "meeting"  # Calendar meetings (read-only from source)


class RecurrencePattern(str, Enum):
    """How often a task recurs."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # For cron-like expressions


class Priority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"  # Must be done, hard deadline
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FLEXIBLE = "flexible"  # Can be moved easily


class TimeSlotPreference(str, Enum):
    """Preferred time of day for scheduling."""

    MORNING = "morning"  # 8am-12pm
    MIDDAY = "midday"  # 12pm-2pm
    AFTERNOON = "afternoon"  # 2pm-5pm
    EVENING = "evening"  # 5pm-9pm
    ANY = "any"


class BaseEntity(BaseModel):
    """Base class for all entities with common fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class SourceTracking(BaseModel):
    """Mixin for tracking external data sources."""

    source_adapter: str  # "google_sheets", "manual", "pdf_parser", etc.
    source_id: Optional[str] = None  # External ID for sync
    last_synced: Optional[datetime] = None
