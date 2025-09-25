"""Utility functions for the scheduler module."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .task import ScheduledTask

logger = logging.getLogger(__name__)


def parse_time_string(time_str: str) -> tuple:
    """
    Parse a time string in various formats.

    Args:
        time_str: Time string (e.g., "14:30", "2:30 PM", "14:30:00")

    Returns:
        Tuple of (hour, minute, second)
    """
    time_str = time_str.strip().upper()

    # Handle AM/PM format
    is_pm = 'PM' in time_str
    is_am = 'AM' in time_str
    time_str = time_str.replace('PM', '').replace('AM', '').strip()

    parts = time_str.split(':')
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0

    # Adjust for PM
    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0

    return hour, minute, second


def resolve_task_dependencies(tasks: List[ScheduledTask]) -> List[ScheduledTask]:
    """
    Resolve task dependencies and return tasks in execution order.

    Args:
        tasks: List of tasks with potential dependencies

    Returns:
        List of tasks in dependency-resolved order
    """
    resolved = []
    unresolved = tasks.copy()

    def resolve_task(task: ScheduledTask):
        if task in resolved:
            return

        # First resolve all dependencies
        for dep in task.depends_on:
            if dep in unresolved:
                resolve_task(dep)

        resolved.append(task)
        if task in unresolved:
            unresolved.remove(task)

    while unresolved:
        task = unresolved[0]
        resolve_task(task)

    return resolved


def calculate_next_run_times(tasks: List[ScheduledTask], days: int = 7) -> Dict[str, List[datetime]]:
    """
    Calculate upcoming run times for tasks.

    Args:
        tasks: List of scheduled tasks
        days: Number of days to look ahead

    Returns:
        Dictionary mapping task ID to list of upcoming run times
    """
    upcoming = {}
    end_date = datetime.now() + timedelta(days=days)

    for task in tasks:
        if not task.enabled:
            continue

        run_times = []
        current_time = task.last_run or datetime.now()

        while len(run_times) < 10:  # Get up to 10 upcoming runs
            next_run = task.schedule.get_next_run_time(current_time)
            if not next_run or next_run > end_date:
                break
            run_times.append(next_run)
            current_time = next_run

        upcoming[task.id] = run_times

    return upcoming


def format_schedule_summary(schedule) -> str:
    """
    Format a human-readable schedule summary.

    Args:
        schedule: Schedule object

    Returns:
        Human-readable schedule description
    """
    from .schedules import (
        IntervalSchedule, CronSchedule, DailySchedule,
        WeeklySchedule, OnceSchedule
    )

    if isinstance(schedule, IntervalSchedule):
        seconds = int(schedule.interval.total_seconds())
        if seconds < 60:
            return f"Every {seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"Every {minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"Every {hours} hour{'s' if hours != 1 else ''}"
        else:
            days = seconds // 86400
            return f"Every {days} day{'s' if days != 1 else ''}"

    elif isinstance(schedule, CronSchedule):
        return f"Cron: {schedule.expression}"

    elif isinstance(schedule, DailySchedule):
        return f"Daily at {schedule.hour:02d}:{schedule.minute:02d}"

    elif isinstance(schedule, WeeklySchedule):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"{days[schedule.weekday]} at {schedule.hour:02d}:{schedule.minute:02d}"

    elif isinstance(schedule, OnceSchedule):
        return f"Once at {schedule.run_at.strftime('%Y-%m-%d %H:%M:%S')}"

    return str(schedule)


def estimate_resource_usage(tasks: List[ScheduledTask], hours: int = 24) -> Dict[str, Any]:
    """
    Estimate resource usage for scheduled tasks.

    Args:
        tasks: List of scheduled tasks
        hours: Time window in hours

    Returns:
        Dictionary with resource usage estimates
    """
    total_executions = 0
    active_tasks = 0
    estimates = {}

    for task in tasks:
        if not task.enabled:
            continue

        active_tasks += 1

        # Estimate executions based on schedule
        from .schedules import IntervalSchedule, DailySchedule, WeeklySchedule

        if isinstance(task.schedule, IntervalSchedule):
            seconds_in_window = hours * 3600
            interval_seconds = task.schedule.interval.total_seconds()
            task_executions = int(seconds_in_window / interval_seconds)
        elif isinstance(task.schedule, DailySchedule):
            task_executions = hours // 24
        elif isinstance(task.schedule, WeeklySchedule):
            task_executions = hours // 168  # Hours in a week
        else:
            task_executions = 1

        total_executions += task_executions
        estimates[task.name] = task_executions

    return {
        'active_tasks': active_tasks,
        'estimated_executions': total_executions,
        'time_window_hours': hours,
        'average_executions_per_hour': total_executions / hours if hours > 0 else 0,
        'task_estimates': estimates
    }


class TaskMonitor:
    """Monitor task execution and performance."""

    def __init__(self):
        self.execution_times: Dict[str, List[float]] = {}
        self.success_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}

    def record_execution(self, task_id: str, execution_time: float, success: bool):
        """Record task execution metrics."""
        if task_id not in self.execution_times:
            self.execution_times[task_id] = []
            self.success_counts[task_id] = 0
            self.failure_counts[task_id] = 0

        self.execution_times[task_id].append(execution_time)

        if success:
            self.success_counts[task_id] += 1
        else:
            self.failure_counts[task_id] += 1

    def get_statistics(self, task_id: str) -> Dict[str, Any]:
        """Get statistics for a specific task."""
        if task_id not in self.execution_times:
            return {}

        times = self.execution_times[task_id]
        total_runs = len(times)
        success_count = self.success_counts[task_id]
        failure_count = self.failure_counts[task_id]

        return {
            'total_runs': total_runs,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_count / total_runs if total_runs > 0 else 0,
            'average_time': sum(times) / len(times) if times else 0,
            'min_time': min(times) if times else 0,
            'max_time': max(times) if times else 0,
            'total_time': sum(times)
        }

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tasks."""
        return {
            task_id: self.get_statistics(task_id)
            for task_id in self.execution_times
        }