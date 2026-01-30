"""Scheduling rules models for configurable priority and preferences."""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from app.models.base import BaseEntity


class RuleConditionType(str, Enum):
    """Types of conditions that can trigger a rule."""

    TASK_TYPE = "task_type"  # Apply to specific task types
    PROJECT_NAME = "project_name"  # Apply to project with name containing value
    TAG = "tag"  # Apply to tasks with tag (future feature)
    DAY_OF_WEEK = "day_of_week"  # Apply on specific days
    TIME_RANGE = "time_range"  # Apply during specific hours
    PRIORITY = "priority"  # Apply to tasks with specific priority


class RuleActionType(str, Enum):
    """Types of actions a rule can perform."""

    PREFER_TIME_SLOT = "prefer_time_slot"  # Prefer morning/afternoon/evening
    AVOID_TIME_SLOT = "avoid_time_slot"  # Avoid certain time slots
    PREFER_DAY = "prefer_day"  # Prefer certain days
    AVOID_DAY = "avoid_day"  # Avoid certain days
    SET_PRIORITY = "set_priority"  # Override priority
    SET_MAX_DAILY_HOURS = "set_max_daily_hours"  # Limit hours per day
    SET_MAX_WEEKLY_HOURS = "set_max_weekly_hours"  # Limit hours per week
    BLOCK_TIME_RANGE = "block_time_range"  # Completely block a time range
    PREFER_TIME_RANGE = "prefer_time_range"  # Prefer a specific time range


class RuleCondition(BaseEntity):
    """A single condition in a scheduling rule."""

    condition_type: RuleConditionType
    value: Any  # Type depends on condition_type
    operator: str = Field(
        default="equals", description="equals, contains, in, not_in, greater_than, less_than"
    )

    def matches(self, context: dict) -> bool:
        """Check if condition matches the given context."""
        actual = context.get(self.condition_type.value)
        if actual is None:
            return False

        match self.operator:
            case "equals":
                return actual == self.value
            case "contains":
                return self.value.lower() in str(actual).lower()
            case "in":
                return actual in self.value
            case "not_in":
                return actual not in self.value
            case "greater_than":
                return actual > self.value
            case "less_than":
                return actual < self.value
            case _:
                return False


class RuleAction(BaseEntity):
    """A single action in a scheduling rule."""

    action_type: RuleActionType
    value: Any  # Type depends on action_type

    def to_dict(self) -> dict:
        """Convert to dict for processing."""
        return {"type": self.action_type.value, "value": self.value}


class SchedulingRule(BaseEntity):
    """A user-defined scheduling rule with conditions and actions."""

    name: str
    description: Optional[str] = None

    # Conditions (AND logic - all must match for rule to apply)
    conditions: list[RuleCondition] = Field(default=[])

    # Actions to apply when conditions match
    actions: list[RuleAction] = Field(default=[])

    # Rule priority (higher = applied later, can override lower priority rules)
    priority: int = Field(default=0, description="Higher priority rules override lower ones")

    is_active: bool = True

    def matches(self, context: dict) -> bool:
        """Check if all conditions match the given context."""
        if not self.conditions:
            return True
        return all(condition.matches(context) for condition in self.conditions)


class SchedulingRuleCreate(BaseEntity):
    """Schema for creating a scheduling rule."""

    name: str
    description: Optional[str] = None
    conditions: list[dict] = []  # Will be converted to RuleCondition
    actions: list[dict] = []  # Will be converted to RuleAction
    priority: int = 0


# Pre-defined rule templates for common use cases
RULE_TEMPLATES = [
    {
        "name": "Morning Focus Work",
        "description": "Schedule focused work like thesis/research in the morning",
        "conditions": [{"condition_type": "project_name", "value": "thesis", "operator": "contains"}],
        "actions": [{"action_type": "prefer_time_slot", "value": "morning"}],
        "priority": 10,
    },
    {
        "name": "Household on Weekends",
        "description": "Keep household tasks on weekends",
        "conditions": [{"condition_type": "task_type", "value": "household", "operator": "equals"}],
        "actions": [
            {"action_type": "prefer_day", "value": [5, 6]},
            {"action_type": "avoid_day", "value": [0, 1, 2, 3, 4]},
        ],
        "priority": 5,
    },
    {
        "name": "No Work After Hours",
        "description": "Stop project work after 4pm on weekdays",
        "conditions": [{"condition_type": "task_type", "value": "project", "operator": "equals"}],
        "actions": [{"action_type": "avoid_time_range", "value": {"start": "16:00", "end": "23:59"}}],
        "priority": 8,
    },
    {
        "name": "Block Class Evenings",
        "description": "Block Wednesday and Thursday evenings for class",
        "conditions": [{"condition_type": "day_of_week", "value": [2, 3], "operator": "in"}],
        "actions": [{"action_type": "block_time_range", "value": {"start": "18:00", "end": "22:00"}}],
        "priority": 100,
    },
    {
        "name": "High Priority First",
        "description": "Schedule high priority tasks in morning slots",
        "conditions": [{"condition_type": "priority", "value": "high", "operator": "equals"}],
        "actions": [{"action_type": "prefer_time_slot", "value": "morning"}],
        "priority": 15,
    },
]
