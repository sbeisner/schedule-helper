"""Smart scheduling engine that respects conflicts, allocation percentages, and task cadence."""

from datetime import datetime, date, timedelta, time
from typing import Optional
from collections import defaultdict
import calendar

from app.db.tables import (
    ProjectTable,
    HouseholdTaskTable,
    AssignmentTable,
    ExternalEventTable,
    TimeBlockTable,
    UserConfigTable,
)
from app.models.calendar import TimeBlock, TimeBlockStatus
from app.models.base import TaskType
from app.services.scheduler.task_time_analyzer import TaskTimeAnalyzer


class SmartScheduler:
    """
    Intelligent scheduler that:
    1. Prevents overlaps with external calendar events
    2. Respects project allocation percentages (monthly)
    3. Schedules household tasks based on recurrence and preferred times
    4. Optimizes for task priorities and deadlines
    """

    def __init__(self, config: UserConfigTable):
        self.config = config
        self.work_start_hour = 8  # Default 8am
        self.work_end_hour = 16  # Default 4pm
        self.min_block_minutes = 30
        self.household_buffer_minutes = 15  # Buffer between household tasks
        self.time_slots = []  # Will be populated per day
        self.scheduled_household_tasks = {}  # Track when each task was last scheduled
        self.time_analyzer = TaskTimeAnalyzer()  # LLM-based task timing analyzer
        self.task_timing_cache = {}  # Cache timing analysis to avoid repeated LLM calls

    def generate_schedule(
        self,
        projects: list[ProjectTable],
        assignments: list[AssignmentTable],
        household_tasks: list[HouseholdTaskTable],
        external_events: list[ExternalEventTable],
        start_date: date,
        end_date: date,
    ) -> list[TimeBlock]:
        """
        Generate an optimized schedule for the date range.

        Args:
            projects: Active projects with remaining hours
            assignments: Incomplete assignments
            household_tasks: Active household tasks
            external_events: Calendar events to avoid conflicts
            start_date: Start of scheduling period
            end_date: End of scheduling period

        Returns:
            List of TimeBlock objects
        """
        blocks = []

        # Analyze household tasks with LLM to determine optimal timing
        print("\n=== Analyzing household task timing with LLM ===")
        for task in household_tasks:
            task_id = str(task.id)
            if task_id not in self.task_timing_cache:
                print(f"Analyzing: {task.name}")
                timing = self.time_analyzer.analyze_task_timing(task.name, task.description)
                self.task_timing_cache[task_id] = timing
                print(f"  → {timing['preferred_time']} ({timing['earliest_hour']}:00 - {timing['latest_hour']}:00)")
                print(f"  → {timing['reasoning']}")
        print()

        # Separate work projects from academic/personal projects
        # Academic projects (from document parsing) should be scheduled in personal time
        work_projects = [p for p in projects if p.source_adapter != 'document_parser']
        academic_projects = [p for p in projects if p.source_adapter == 'document_parser']

        # Calculate monthly project allocations for work projects only
        project_monthly_hours = self._calculate_project_monthly_allocations(
            work_projects, start_date, end_date
        )

        # Track hours scheduled per project this month
        project_hours_scheduled = defaultdict(float)

        # Generate schedule day by day
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            is_weekend = day_of_week >= 5

            # Get external events for this day
            day_events = self._get_events_for_day(external_events, current_date)

            day_blocks = []

            # Generate personal time slots (for household tasks and assignments)
            personal_slots = self._generate_available_slots(current_date, day_events, is_weekend, work_hours_only=False)

            # On weekdays, prioritize assignments and academic projects over household tasks
            # On weekends, schedule household tasks first
            if not is_weekend:
                # 1. Schedule assignments first in evening time
                assignment_blocks = self._schedule_assignments_for_day(
                    assignments, current_date, personal_slots
                )
                day_blocks.extend(assignment_blocks)

                # 2. Schedule academic projects in remaining evening time
                remaining_slots = self._remove_scheduled_blocks(personal_slots, assignment_blocks)
                academic_project_blocks = self._schedule_projects_for_day(
                    academic_projects,
                    current_date,
                    remaining_slots,
                    {},  # No allocation tracking for academic projects
                    {},
                )
                day_blocks.extend(academic_project_blocks)

                # 3. Schedule household tasks in any remaining personal time
                remaining_slots = self._remove_scheduled_blocks(remaining_slots, academic_project_blocks)
                household_blocks = self._schedule_household_tasks_for_day(
                    household_tasks, current_date, day_of_week, remaining_slots, is_weekend
                )
                day_blocks.extend(household_blocks)
            else:
                # Weekend: household tasks first
                household_blocks = self._schedule_household_tasks_for_day(
                    household_tasks, current_date, day_of_week, personal_slots, is_weekend
                )
                day_blocks.extend(household_blocks)

                # Then assignments
                remaining_slots = self._remove_scheduled_blocks(personal_slots, household_blocks)
                assignment_blocks = self._schedule_assignments_for_day(
                    assignments, current_date, remaining_slots
                )
                day_blocks.extend(assignment_blocks)

                # Then academic projects
                remaining_slots = self._remove_scheduled_blocks(remaining_slots, assignment_blocks)
                academic_project_blocks = self._schedule_projects_for_day(
                    academic_projects,
                    current_date,
                    remaining_slots,
                    {},  # No allocation tracking
                    {},
                )
                day_blocks.extend(academic_project_blocks)

            if not is_weekend:
                # Weekdays: schedule WORK projects during work hours only
                work_slots = self._generate_available_slots(current_date, day_events, is_weekend, work_hours_only=True)

                work_project_blocks = self._schedule_projects_for_day(
                    work_projects,
                    current_date,
                    work_slots,
                    project_monthly_hours,
                    project_hours_scheduled,
                )
                day_blocks.extend(work_project_blocks)
            else:
                # Weekends: work projects can use remaining personal time
                remaining_slots = self._remove_scheduled_blocks(remaining_slots, academic_project_blocks)
                work_project_blocks = self._schedule_projects_for_day(
                    work_projects,
                    current_date,
                    remaining_slots,
                    project_monthly_hours,
                    project_hours_scheduled,
                )
                day_blocks.extend(work_project_blocks)

            blocks.extend(day_blocks)
            current_date += timedelta(days=1)

        return blocks

    def _calculate_project_monthly_allocations(
        self, projects: list[ProjectTable], start_date: date, end_date: date
    ) -> dict[str, float]:
        """
        Calculate how many hours each project should get based on allocation percentage.

        allocation_percentage=25% means "25% of total work hours this month"

        Returns:
            Dict mapping project_id to target hours for the period
        """
        # Calculate total work hours in the period
        total_work_hours = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Weekday
                total_work_hours += 8  # 8 hours per work day

            current += timedelta(days=1)

        # Calculate target hours for each project
        allocations = {}
        for project in projects:
            target_hours = (project.allocation_percentage / 100.0) * total_work_hours

            # Cap at remaining hours needed
            hours_remaining = project.total_hours_allocated - project.hours_used
            actual_hours = min(target_hours, hours_remaining)

            allocations[str(project.id)] = actual_hours

        return allocations

    def _get_life_necessity_blocks(
        self, target_date: date, is_weekend: bool
    ) -> list[tuple[datetime, datetime]]:
        """
        Get blocked times for basic life necessities (meals, sleep prep, shower).

        These are non-negotiable time blocks that should never have tasks scheduled.

        Returns:
            List of (start_time, end_time) tuples for blocked times
        """
        blocks = []

        # Morning routine: 7:00-8:00 AM (shower, breakfast, prep)
        blocks.append((
            datetime.combine(target_date, time(7, 0)),
            datetime.combine(target_date, time(8, 0))
        ))

        # Lunch: 12:00-1:00 PM
        blocks.append((
            datetime.combine(target_date, time(12, 0)),
            datetime.combine(target_date, time(13, 0))
        ))

        # Dinner: 6:00-7:00 PM
        blocks.append((
            datetime.combine(target_date, time(18, 0)),
            datetime.combine(target_date, time(19, 0))
        ))

        # Evening wind-down and sleep prep: 9:00 PM onwards
        # (Don't schedule anything after 9 PM)
        blocks.append((
            datetime.combine(target_date, time(21, 0)),
            datetime.combine(target_date, time(23, 59))
        ))

        return blocks

    def _get_events_for_day(
        self, external_events: list[ExternalEventTable], target_date: date
    ) -> list[ExternalEventTable]:
        """Get all external events that occur on the target date."""
        day_events = []
        for event in external_events:
            event_date = event.start_time.date()
            if event_date == target_date:
                day_events.append(event)
        return day_events

    def _remove_scheduled_blocks(
        self, available_slots: list[tuple[datetime, datetime]], scheduled_blocks: list[TimeBlock]
    ) -> list[tuple[datetime, datetime]]:
        """Remove scheduled blocks from available slots."""
        remaining_slots = available_slots.copy()

        for block in scheduled_blocks:
            new_slots = []
            for slot_start, slot_end in remaining_slots:
                # Check if block overlaps with this slot
                if block.end_time <= slot_start or block.start_time >= slot_end:
                    # No overlap, keep the slot
                    new_slots.append((slot_start, slot_end))
                else:
                    # Block overlaps, split the slot
                    if block.start_time > slot_start:
                        # Add slot before block
                        new_slots.append((slot_start, block.start_time))
                    if block.end_time < slot_end:
                        # Add slot after block
                        new_slots.append((block.end_time, slot_end))
            remaining_slots = new_slots

        return remaining_slots

    def _generate_available_slots(
        self, target_date: date, external_events: list[ExternalEventTable], is_weekend: bool,
        work_hours_only: bool = False
    ) -> list[tuple[datetime, datetime]]:
        """
        Generate available time slots for the day, avoiding external events and life necessities.

        Args:
            target_date: The date to generate slots for
            external_events: Calendar events to avoid
            is_weekend: Whether this is a weekend day
            work_hours_only: If True, only return work hours (for projects). If False, return personal time.

        Returns:
            List of (start_time, end_time) tuples representing free slots
        """
        # Define basic life rules - blocked times for everyone
        life_blocks = self._get_life_necessity_blocks(target_date, is_weekend)

        if is_weekend:
            # Weekends: all day available for personal tasks
            day_start = datetime.combine(target_date, time(9, 0))
            day_end = datetime.combine(target_date, time(21, 0))  # Until 9 PM
            free_slots = [(day_start, day_end)]
        elif work_hours_only:
            # Weekday work hours: only for projects
            day_start = datetime.combine(target_date, time(self.work_start_hour, 0))
            day_end = datetime.combine(target_date, time(self.work_end_hour, 0))
            free_slots = [(day_start, day_end)]
        else:
            # Weekday personal time: before and after work for assignments/household
            morning_start = datetime.combine(target_date, time(8, 0))  # After morning routine
            morning_end = datetime.combine(target_date, time(self.work_start_hour, 0))

            evening_start = datetime.combine(target_date, time(self.work_end_hour, 0))
            evening_end = datetime.combine(target_date, time(21, 0))  # Until 9 PM

            free_slots = [(evening_start, evening_end)]  # Prioritize evening time for assignments

        # Remove life necessity blocks
        for block_start, block_end in life_blocks:
            new_slots = []
            for slot_start, slot_end in free_slots:
                if block_end <= slot_start or block_start >= slot_end:
                    # No overlap
                    new_slots.append((slot_start, slot_end))
                else:
                    # Block overlaps, split the slot
                    if block_start > slot_start:
                        new_slots.append((slot_start, block_start))
                    if block_end < slot_end:
                        new_slots.append((block_end, slot_end))
            free_slots = new_slots

        # Remove external event times
        for event in external_events:
            new_slots = []
            for slot_start, slot_end in free_slots:
                # Check if event overlaps with this slot
                if event.end_time <= slot_start or event.start_time >= slot_end:
                    # No overlap, keep the slot
                    new_slots.append((slot_start, slot_end))
                else:
                    # Event overlaps, split the slot
                    if event.start_time > slot_start:
                        # Add slot before event
                        new_slots.append((slot_start, event.start_time))

                    if event.end_time < slot_end:
                        # Add slot after event
                        new_slots.append((event.end_time, slot_end))

            free_slots = new_slots

        # Filter out slots that are too small (< 30 minutes)
        free_slots = [
            (start, end)
            for start, end in free_slots
            if (end - start).total_seconds() >= self.min_block_minutes * 60
        ]

        return free_slots

    def _schedule_household_tasks_for_day(
        self,
        tasks: list[HouseholdTaskTable],
        target_date: date,
        day_of_week: int,
        available_slots: list[tuple[datetime, datetime]],
        is_weekend: bool,
    ) -> list[TimeBlock]:
        """
        Intelligently schedule household tasks with proper spacing and recurrence logic.

        Daily tasks: Schedule every day
        Weekly tasks: Schedule once per week (distribute across weekend days)
        Bi-weekly tasks: Schedule once every 2 weeks
        Monthly tasks: Schedule once per month

        Args:
            tasks: List of active household tasks
            target_date: The date to schedule for
            day_of_week: 0=Monday, 6=Sunday
            available_slots: Available time slots for this day
            is_weekend: Whether this is a weekend day

        Returns:
            List of TimeBlock objects for household tasks
        """
        blocks = []
        slot_idx = 0

        # Separate daily tasks from periodic tasks (weekly, bi-weekly, monthly)
        daily_tasks = [t for t in tasks if t.recurrence == "daily"]
        periodic_tasks = [t for t in tasks if t.recurrence != "daily"]

        # Sort tasks by timing flexibility (least flexible first)
        # This ensures time-constrained tasks (e.g., breakfast dishes) get scheduled before flexible ones
        def get_timing_flexibility(task):
            task_id = str(task.id)
            if task_id in self.task_timing_cache:
                timing = self.task_timing_cache[task_id]
                # Calculate time window size (smaller = less flexible = higher priority)
                window_size = timing['latest_hour'] - timing['earliest_hour']
                return window_size
            return 24  # Default to most flexible if no timing data

        daily_tasks.sort(key=get_timing_flexibility)
        periodic_tasks.sort(key=get_timing_flexibility)

        # Daily tasks: schedule on ANY day (weekday or weekend)
        for task in daily_tasks:
            # Check if this task was already scheduled recently (at least 1 day ago)
            if not self._should_schedule_task_today(task, target_date):
                continue

            # Limit daily tasks per day
            if len(blocks) >= 2:
                break

            if slot_idx >= len(available_slots):
                break

            # Schedule the daily task
            result = self._create_task_block(task, available_slots, slot_idx, target_date)
            if result:
                time_block, remaining_slot = result
                blocks.append(time_block)
                # Update slot tracking based on whether we used the whole slot
                if remaining_slot:  # If there's a remaining slot
                    available_slots[slot_idx] = remaining_slot
                else:
                    slot_idx += 1

        # Periodic tasks (weekly, bi-weekly, monthly): only on weekends
        # Distribute across Saturday and Sunday by limiting to 2 periodic tasks per day
        if is_weekend:
            periodic_blocks_today = 0
            max_periodic_per_day = 2  # Limit to 2 periodic tasks per weekend day

            for task in periodic_tasks:
                # Check if this task should be scheduled today based on recurrence rules
                if not self._should_schedule_task_today(task, target_date):
                    continue

                # Limit periodic tasks per weekend day to distribute across both days
                if periodic_blocks_today >= max_periodic_per_day:
                    break

                # Check total blocks limit
                if len(blocks) >= 4:
                    break

                if slot_idx >= len(available_slots):
                    break

                # Schedule the periodic task
                result = self._create_task_block(task, available_slots, slot_idx, target_date)
                if result:
                    time_block, remaining_slot = result
                    blocks.append(time_block)
                    periodic_blocks_today += 1
                    # Update slot tracking
                    if remaining_slot:  # If there's a remaining slot
                        available_slots[slot_idx] = remaining_slot
                    else:
                        slot_idx += 1

        return blocks

    def _create_task_block(
        self,
        task: HouseholdTaskTable,
        available_slots: list[tuple[datetime, datetime]],
        slot_idx: int,
        target_date: date,
    ) -> tuple[TimeBlock, Optional[tuple[datetime, datetime]]]:
        """
        Create a time block for a household task.

        Returns:
            Tuple of (TimeBlock, remaining_slot) or None if task doesn't fit
            remaining_slot is None if the entire slot was used
        """
        if slot_idx >= len(available_slots):
            return None

        slot_start, slot_end = available_slots[slot_idx]

        # Check if task's timing preferences match this time slot
        if not self._task_timing_matches_slot(task, slot_start):
            return None

        # Calculate task duration + buffer
        task_duration = timedelta(minutes=task.estimated_duration_minutes)
        buffer = timedelta(minutes=self.household_buffer_minutes)

        # Check if task + buffer fits in this slot
        task_end = slot_start + task_duration
        slot_needed_end = task_end + buffer

        if slot_needed_end <= slot_end:
            # Create time block
            block = TimeBlock(
                task_type=TaskType.HOUSEHOLD,
                task_id=str(task.id),
                task_name=task.name,
                start_time=slot_start,
                end_time=task_end,
                status=TimeBlockStatus.SCHEDULED,
            )

            # Track that we scheduled this task
            self.scheduled_household_tasks[str(task.id)] = target_date

            # Calculate remaining slot
            remaining_time = (slot_end - slot_needed_end).total_seconds() / 60
            if remaining_time >= self.min_block_minutes:
                remaining_slot = (slot_needed_end, slot_end)
            else:
                remaining_slot = None

            return (block, remaining_slot)

        return None

    def _should_schedule_task_today(self, task: HouseholdTaskTable, target_date: date) -> bool:
        """
        Determine if a task should be scheduled today based on recurrence rules.

        Args:
            task: The household task
            target_date: The date being scheduled

        Returns:
            True if task should be scheduled, False otherwise
        """
        task_id = str(task.id)

        # If we haven't scheduled this task yet, allow it
        if task_id not in self.scheduled_household_tasks:
            return True

        last_scheduled = self.scheduled_household_tasks[task_id]
        days_since_last = (target_date - last_scheduled).days

        # Check recurrence rules
        if task.recurrence == "daily":
            return days_since_last >= 1
        elif task.recurrence == "weekly":
            return days_since_last >= 7
        elif task.recurrence == "biweekly":
            return days_since_last >= 14
        elif task.recurrence == "monthly":
            return days_since_last >= 30
        else:
            # Unknown recurrence, default to weekly
            return days_since_last >= 7

    def _task_timing_matches_slot(self, task: HouseholdTaskTable, slot_start: datetime) -> bool:
        """
        Check if a task's timing preferences allow it to be scheduled in this time slot.

        Args:
            task: The household task
            slot_start: Start time of the available slot

        Returns:
            True if the task can be scheduled at this time, False otherwise
        """
        task_id = str(task.id)

        # If we don't have timing analysis for this task, allow it (fallback)
        if task_id not in self.task_timing_cache:
            return True

        timing = self.task_timing_cache[task_id]
        slot_hour = slot_start.hour

        # Check if slot hour is within the task's preferred time range
        if slot_hour < timing['earliest_hour'] or slot_hour >= timing['latest_hour']:
            print(f"  ⚠ Skipping '{task.name}': slot hour {slot_hour} outside range {timing['earliest_hour']}-{timing['latest_hour']}")
            return False

        return True

    def _schedule_assignments_for_day(
        self,
        assignments: list[AssignmentTable],
        target_date: date,
        available_slots: list[tuple[datetime, datetime]],
    ) -> list[TimeBlock]:
        """Schedule assignments that are due soon."""
        blocks = []

        # Sort by due date (earliest first)
        urgent_assignments = sorted(
            [a for a in assignments if (a.due_date.date() - target_date).days <= 7],
            key=lambda x: x.due_date,
        )

        for assignment in urgent_assignments[:2]:  # Max 2 assignments per day
            if not available_slots:
                break

            slot_start, slot_end = available_slots.pop(0)

            # Default 2-hour blocks for assignments
            duration = timedelta(hours=2)
            task_end = slot_start + duration

            if task_end <= slot_end:
                block = TimeBlock(
                    task_type=TaskType.ASSIGNMENT,
                    task_id=str(assignment.id),
                    task_name=assignment.name,
                    start_time=slot_start,
                    end_time=task_end,
                    status=TimeBlockStatus.SCHEDULED,
                )
                blocks.append(block)

                # Add remaining slot time back if any
                if task_end < slot_end:
                    available_slots.insert(0, (task_end, slot_end))

        return blocks

    def _schedule_projects_for_day(
        self,
        projects: list[ProjectTable],
        target_date: date,
        available_slots: list[tuple[datetime, datetime]],
        project_monthly_hours: dict[str, float],
        project_hours_scheduled: dict[str, float],
    ) -> list[TimeBlock]:
        """
        Schedule project work based on allocation percentages.

        Prioritizes projects that are behind on their allocation target.
        """
        blocks = []

        # Sort projects by: (1) how far behind they are on allocation, (2) priority
        projects_with_deficit = []
        for project in projects:
            project_id = str(project.id)
            target_hours = project_monthly_hours.get(project_id, 0)
            scheduled_hours = project_hours_scheduled.get(project_id, 0)
            deficit = target_hours - scheduled_hours
            hours_remaining = project.total_hours_allocated - project.hours_used

            if deficit > 0 and hours_remaining > 0:
                projects_with_deficit.append((deficit, project))

        # Sort by deficit (descending)
        projects_with_deficit.sort(key=lambda x: -x[0])

        for deficit, project in projects_with_deficit:
            if not available_slots:
                break

            slot_start, slot_end = available_slots.pop(0)

            # Calculate block duration (1.5-2 hours, or whatever fits)
            hours_remaining = project.total_hours_allocated - project.hours_used
            slot_duration_hours = (slot_end - slot_start).total_seconds() / 3600
            block_hours = min(2.0, slot_duration_hours, hours_remaining, deficit)

            if block_hours < 0.5:  # Skip if less than 30 minutes
                available_slots.insert(0, (slot_start, slot_end))
                continue

            task_end = slot_start + timedelta(hours=block_hours)

            block = TimeBlock(
                task_type=TaskType.PROJECT,
                task_id=str(project.id),
                task_name=project.name,
                start_time=slot_start,
                end_time=task_end,
                status=TimeBlockStatus.SCHEDULED,
            )
            blocks.append(block)

            # Update tracking
            project_hours_scheduled[str(project.id)] += block_hours

            # Add remaining slot time back if any
            remaining_time = (slot_end - task_end).total_seconds() / 60
            if remaining_time >= self.min_block_minutes:
                available_slots.insert(0, (task_end, slot_end))

        return blocks
