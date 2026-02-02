"""User configuration models."""

from datetime import datetime, time, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class WorkSchedule(BaseModel):
    """A user's work schedule for a specific day."""

    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time = Field(default=time(8, 0))  # 8:00 AM default
    end_time: time = Field(default=time(16, 0))  # 4:00 PM default
    is_working_day: bool = True

    model_config = {"from_attributes": True}


class UserConfig(BaseModel):
    """User configuration and preferences."""

    id: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Work schedule (one entry per day of week)
    work_schedules: list[WorkSchedule] = Field(default=[])
    default_work_hours_per_day: float = Field(default=8.0, ge=0, le=24)

    # Scheduling preferences
    min_break_between_blocks_minutes: int = Field(default=15, ge=0)
    preferred_block_duration_minutes: int = Field(default=90, ge=15, le=480)
    max_daily_scheduled_hours: float = Field(default=10.0, ge=0, le=24)

    # Buffer preferences around meetings
    meeting_buffer_before_minutes: int = Field(default=10, ge=0)
    meeting_buffer_after_minutes: int = Field(default=5, ge=0)

    # Google integration
    google_calendar_id: str = Field(default="primary")
    google_sheets_projects_id: Optional[str] = None
    google_sheets_projects_range: str = Field(default="Projects!A2:J")
    google_sheets_household_id: Optional[str] = None
    google_sheets_household_range: str = Field(default="Household!A2:H")

    # Auto-scheduling settings
    auto_schedule_enabled: bool = True
    schedule_horizon_days: int = Field(default=14, ge=1, le=90)
    auto_sync_interval_minutes: int = Field(default=30, ge=5)

    # Timezone
    timezone: str = Field(default="America/New_York")

    model_config = {"from_attributes": True}

    @property
    def min_break_between_blocks(self) -> timedelta:
        return timedelta(minutes=self.min_break_between_blocks_minutes)

    @property
    def preferred_block_duration(self) -> timedelta:
        return timedelta(minutes=self.preferred_block_duration_minutes)

    @property
    def meeting_buffer_before(self) -> timedelta:
        return timedelta(minutes=self.meeting_buffer_before_minutes)

    @property
    def meeting_buffer_after(self) -> timedelta:
        return timedelta(minutes=self.meeting_buffer_after_minutes)

    @classmethod
    def create_default(cls) -> "UserConfig":
        """Create default configuration for a standard 8am-4pm M-F work schedule."""
        schedules = []
        for day in range(7):
            is_working = day < 5  # Monday-Friday
            schedules.append(
                WorkSchedule(
                    day_of_week=day,
                    start_time=time(8, 0) if is_working else time(9, 0),
                    end_time=time(16, 0) if is_working else time(17, 0),
                    is_working_day=is_working,
                )
            )
        return cls(work_schedules=schedules)


class UserConfigUpdate(BaseModel):
    """Schema for updating user configuration."""

    work_schedules: Optional[list[WorkSchedule]] = None
    default_work_hours_per_day: Optional[float] = None
    min_break_between_blocks_minutes: Optional[int] = None
    preferred_block_duration_minutes: Optional[int] = None
    max_daily_scheduled_hours: Optional[float] = None
    meeting_buffer_before_minutes: Optional[int] = None
    meeting_buffer_after_minutes: Optional[int] = None
    google_calendar_id: Optional[str] = None
    google_sheets_projects_id: Optional[str] = None
    google_sheets_projects_range: Optional[str] = None
    google_sheets_household_id: Optional[str] = None
    google_sheets_household_range: Optional[str] = None
    auto_schedule_enabled: Optional[bool] = None
    schedule_horizon_days: Optional[int] = None
    auto_sync_interval_minutes: Optional[int] = None
    timezone: Optional[str] = None
