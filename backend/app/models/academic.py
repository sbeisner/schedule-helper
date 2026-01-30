"""Academic models for courses and assignments."""

from datetime import date, datetime, time, timedelta
from typing import Optional

from pydantic import Field, computed_field

from app.models.base import BaseEntity, Priority, SourceTracking, TimeSlotPreference


class Course(BaseEntity, SourceTracking):
    """An academic course with fixed schedule."""

    code: str  # e.g., "ST.778"
    name: str  # e.g., "Time Series Analysis"

    # Schedule
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    location: Optional[str] = None  # e.g., "Online via Zoom"

    # Semester bounds
    semester_start: date
    semester_end: date

    # Breaks/exceptions (dates when class doesn't meet)
    excluded_dates: list[date] = Field(default=[])

    # Links
    syllabus_path: Optional[str] = None  # Path to PDF
    moodle_url: Optional[str] = None

    @computed_field
    @property
    def duration(self) -> timedelta:
        """Calculate class duration."""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return end_dt - start_dt

    def get_class_dates(self) -> list[date]:
        """Generate all class dates for the semester."""
        dates = []
        current = self.semester_start

        # Find first occurrence of the day_of_week
        while current.weekday() != self.day_of_week:
            current += timedelta(days=1)

        # Generate all occurrences
        while current <= self.semester_end:
            if current not in self.excluded_dates:
                dates.append(current)
            current += timedelta(weeks=1)

        return dates


class Assignment(BaseEntity):
    """A course assignment with deadline."""

    course_id: str  # UUID as string for flexibility
    name: str  # e.g., "HW#1", "Progress Report #1"
    description: Optional[str] = None

    # Deadline
    due_date: datetime

    # Time estimation
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    hours_logged: float = Field(default=0, ge=0)

    # Scheduling
    priority: Priority = Priority.HIGH
    preferred_time_slots: list[TimeSlotPreference] = Field(default=[TimeSlotPreference.ANY])

    # Status
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    @computed_field
    @property
    def hours_remaining(self) -> Optional[float]:
        """Calculate remaining estimated hours."""
        if self.estimated_hours is None:
            return None
        return max(0, self.estimated_hours - self.hours_logged)

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if assignment is past due."""
        return not self.is_completed and datetime.utcnow() > self.due_date

    @computed_field
    @property
    def days_until_due(self) -> int:
        """Days until deadline (negative if overdue)."""
        delta = self.due_date.date() - date.today()
        return delta.days


class CourseCreate(BaseEntity):
    """Schema for creating a new course."""

    code: str
    name: str
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    location: Optional[str] = None
    semester_start: date
    semester_end: date
    excluded_dates: list[date] = []


class AssignmentCreate(BaseEntity):
    """Schema for creating a new assignment."""

    course_id: str
    name: str
    description: Optional[str] = None
    due_date: datetime
    estimated_hours: Optional[float] = None
    priority: Priority = Priority.HIGH
