"""Decorators for scheduling functions."""

from functools import wraps
from typing import Callable, Optional, Any, Union
from datetime import datetime

from .schedules import IntervalSchedule, CronSchedule, DailySchedule, WeeklySchedule
from .core import TaskScheduler
from .task import RetryPolicy


# Global scheduler for decorator usage
_global_scheduler: Optional[TaskScheduler] = None


def get_global_scheduler() -> TaskScheduler:
    """Get or create the global scheduler."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TaskScheduler()
    return _global_scheduler


def set_global_scheduler(scheduler: TaskScheduler):
    """Set the global scheduler."""
    global _global_scheduler
    _global_scheduler = scheduler


def schedule(
    scheduler: Optional[TaskScheduler] = None,
    name: Optional[str] = None,
    enabled: bool = True,
    max_runs: Optional[int] = None,
    retry_policy: Optional[RetryPolicy] = None,
    priority: int = 0
):
    """
    Base decorator for scheduling functions.

    Args:
        scheduler: TaskScheduler instance (uses global if not provided)
        name: Task name (uses function name if not provided)
        enabled: Whether task starts enabled
        max_runs: Maximum number of executions
        retry_policy: Retry policy for failures
        priority: Task priority

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Store scheduling info on the function
        func._scheduled = True
        func._scheduler = scheduler or get_global_scheduler()
        func._task_name = name or func.__name__
        func._task_enabled = enabled
        func._max_runs = max_runs
        func._retry_policy = retry_policy
        func._priority = priority
        func._task = None  # Will be set when task is added

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function normally when called directly
            return func(*args, **kwargs)

        # Add method to start scheduling
        def start_scheduling(schedule_obj):
            """Start scheduling this function."""
            if not hasattr(func, '_scheduler'):
                raise RuntimeError("Function is not decorated with a scheduler")

            task = func._scheduler.add_task(
                name=func._task_name,
                callable_obj=func,
                schedule=schedule_obj,
                enabled=func._task_enabled,
                max_runs=func._max_runs,
                retry_policy=func._retry_policy,
                priority=func._priority
            )
            func._task = task
            return task

        wrapper.start_scheduling = start_scheduling
        wrapper._scheduled = True

        return wrapper

    return decorator


def every(
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
    weeks: int = 0,
    scheduler: Optional[TaskScheduler] = None,
    name: Optional[str] = None,
    enabled: bool = True,
    max_runs: Optional[int] = None,
    retry_policy: Optional[RetryPolicy] = None,
    priority: int = 0,
    start_immediately: bool = True
):
    """
    Decorator to schedule a function at fixed intervals.

    Args:
        seconds: Interval in seconds
        minutes: Interval in minutes
        hours: Interval in hours
        days: Interval in days
        weeks: Interval in weeks
        scheduler: TaskScheduler instance
        name: Task name
        enabled: Whether task starts enabled
        max_runs: Maximum executions
        retry_policy: Retry policy
        priority: Task priority
        start_immediately: Whether to start scheduling immediately

    Example:
        @every(minutes=30)
        def sync_data():
            print("Syncing data...")
    """
    def decorator(func: Callable) -> Callable:
        # Apply base scheduling decorator
        scheduled_func = schedule(
            scheduler=scheduler,
            name=name,
            enabled=enabled,
            max_runs=max_runs,
            retry_policy=retry_policy,
            priority=priority
        )(func)

        # Create interval schedule
        interval_schedule = IntervalSchedule(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks
        )

        # Start scheduling if requested
        if start_immediately:
            task = scheduled_func.start_scheduling(interval_schedule)
            scheduled_func._task = task

        # Store schedule on function
        scheduled_func._schedule = interval_schedule

        return scheduled_func

    return decorator


def cron(
    expression: str,
    scheduler: Optional[TaskScheduler] = None,
    name: Optional[str] = None,
    enabled: bool = True,
    max_runs: Optional[int] = None,
    retry_policy: Optional[RetryPolicy] = None,
    priority: int = 0,
    start_immediately: bool = True
):
    """
    Decorator to schedule a function using cron expression.

    Args:
        expression: Cron expression (e.g., "0 9 * * MON-FRI")
        scheduler: TaskScheduler instance
        name: Task name
        enabled: Whether task starts enabled
        max_runs: Maximum executions
        retry_policy: Retry policy
        priority: Task priority
        start_immediately: Whether to start scheduling immediately

    Example:
        @cron("0 9 * * MON-FRI")  # 9 AM on weekdays
        def morning_report():
            print("Generating morning report...")
    """
    def decorator(func: Callable) -> Callable:
        # Apply base scheduling decorator
        scheduled_func = schedule(
            scheduler=scheduler,
            name=name,
            enabled=enabled,
            max_runs=max_runs,
            retry_policy=retry_policy,
            priority=priority
        )(func)

        # Create cron schedule
        cron_schedule = CronSchedule(expression)

        # Start scheduling if requested
        if start_immediately:
            task = scheduled_func.start_scheduling(cron_schedule)
            scheduled_func._task = task

        # Store schedule on function
        scheduled_func._schedule = cron_schedule

        return scheduled_func

    return decorator


def daily(
    hour: int,
    minute: int = 0,
    second: int = 0,
    scheduler: Optional[TaskScheduler] = None,
    name: Optional[str] = None,
    enabled: bool = True,
    max_runs: Optional[int] = None,
    retry_policy: Optional[RetryPolicy] = None,
    priority: int = 0,
    start_immediately: bool = True
):
    """
    Decorator to schedule a function daily at specific time.

    Args:
        hour: Hour of day (0-23)
        minute: Minute of hour (0-59)
        second: Second of minute (0-59)
        scheduler: TaskScheduler instance
        name: Task name
        enabled: Whether task starts enabled
        max_runs: Maximum executions
        retry_policy: Retry policy
        priority: Task priority
        start_immediately: Whether to start scheduling immediately

    Example:
        @daily(hour=2, minute=30)  # 2:30 AM daily
        def nightly_backup():
            print("Running backup...")
    """
    def decorator(func: Callable) -> Callable:
        # Apply base scheduling decorator
        scheduled_func = schedule(
            scheduler=scheduler,
            name=name,
            enabled=enabled,
            max_runs=max_runs,
            retry_policy=retry_policy,
            priority=priority
        )(func)

        # Create daily schedule
        daily_schedule = DailySchedule(hour, minute, second)

        # Start scheduling if requested
        if start_immediately:
            task = scheduled_func.start_scheduling(daily_schedule)
            scheduled_func._task = task

        # Store schedule on function
        scheduled_func._schedule = daily_schedule

        return scheduled_func

    return decorator


def weekly(
    weekday: Union[str, int],
    hour: int,
    minute: int = 0,
    scheduler: Optional[TaskScheduler] = None,
    name: Optional[str] = None,
    enabled: bool = True,
    max_runs: Optional[int] = None,
    retry_policy: Optional[RetryPolicy] = None,
    priority: int = 0,
    start_immediately: bool = True
):
    """
    Decorator to schedule a function weekly at specific day and time.

    Args:
        weekday: Day of week (0=Monday, 6=Sunday) or name
        hour: Hour of day (0-23)
        minute: Minute of hour (0-59)
        scheduler: TaskScheduler instance
        name: Task name
        enabled: Whether task starts enabled
        max_runs: Maximum executions
        retry_policy: Retry policy
        priority: Task priority
        start_immediately: Whether to start scheduling immediately

    Example:
        @weekly("monday", 9, 0)  # Monday at 9:00 AM
        def weekly_report():
            print("Generating weekly report...")
    """
    def decorator(func: Callable) -> Callable:
        # Apply base scheduling decorator
        scheduled_func = schedule(
            scheduler=scheduler,
            name=name,
            enabled=enabled,
            max_runs=max_runs,
            retry_policy=retry_policy,
            priority=priority
        )(func)

        # Create weekly schedule
        weekly_schedule = WeeklySchedule(weekday, hour, minute)

        # Start scheduling if requested
        if start_immediately:
            task = scheduled_func.start_scheduling(weekly_schedule)
            scheduled_func._task = task

        # Store schedule on function
        scheduled_func._schedule = weekly_schedule

        return scheduled_func

    return decorator