"""Builder pattern for creating scheduled tasks with a fluent interface."""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from .core import TaskScheduler
from .schedules import (
    Schedule,
    IntervalSchedule,
    CronSchedule,
    DailySchedule,
    WeeklySchedule,
    OnceSchedule
)
from .task import ScheduledTask, RetryPolicy
from ..batch import CallableWrapper


class TaskBuilder:
    """
    Builder class for creating scheduled tasks with a fluent interface.

    Example:
        scheduler.add_task()
            .named("Daily Sync")
            .calling(sync_function)
            .with_args(arg1, arg2, key="value")
            .every(hours=24)
            .at_time("02:00")
            .with_retries(3, delay=60)
            .on_error(error_handler)
            .on_success(success_handler)
            .with_priority(10)
            .start()
    """

    def __init__(self, scheduler: TaskScheduler):
        """Initialize the task builder."""
        self.scheduler = scheduler
        self.name: Optional[str] = None
        self.callable_obj: Optional[Union[Callable, CallableWrapper]] = None
        self.args: tuple = ()
        self.kwargs: dict = {}
        self.schedule: Optional[Schedule] = None
        self.enabled: bool = True
        self.max_runs: Optional[int] = None
        self.retry_policy: Optional[RetryPolicy] = None
        self.on_success_callback: Optional[Callable] = None
        self.on_failure_callback: Optional[Callable] = None
        self.metadata: Dict[str, Any] = {}
        self.depends_on: List[ScheduledTask] = []
        self.priority: int = 0
        self._task: Optional[ScheduledTask] = None

    def named(self, name: str) -> 'TaskBuilder':
        """Set the task name."""
        self.name = name
        return self

    def calling(self, func: Union[Callable, CallableWrapper]) -> 'TaskBuilder':
        """Set the function or CallableWrapper to execute."""
        self.callable_obj = func
        return self

    def with_args(self, *args, **kwargs) -> 'TaskBuilder':
        """Set arguments for the callable."""
        self.args = args
        self.kwargs = kwargs
        return self

    def every(
        self,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        weeks: int = 0
    ) -> 'TaskBuilder':
        """Set an interval-based schedule."""
        self.schedule = IntervalSchedule(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks
        )
        return self

    def at_time(self, time_str: str) -> 'TaskBuilder':
        """
        Set a specific time for daily execution.

        Args:
            time_str: Time string in format "HH:MM" or "HH:MM:SS"
        """
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0

        # If we already have an interval schedule, convert to daily
        if isinstance(self.schedule, IntervalSchedule):
            # Check if it's a daily interval
            if self.schedule.interval.days == 1:
                self.schedule = DailySchedule(hour, minute, second)
        else:
            self.schedule = DailySchedule(hour, minute, second)

        return self

    def using_cron(self, expression: str) -> 'TaskBuilder':
        """Set a cron-based schedule."""
        self.schedule = CronSchedule(expression)
        return self

    def daily_at(self, hour: int, minute: int = 0, second: int = 0) -> 'TaskBuilder':
        """Set a daily schedule at specific time."""
        self.schedule = DailySchedule(hour, minute, second)
        return self

    def weekly_on(
        self,
        weekday: Union[str, int],
        hour: int,
        minute: int = 0
    ) -> 'TaskBuilder':
        """Set a weekly schedule on specific day and time."""
        self.schedule = WeeklySchedule(weekday, hour, minute)
        return self

    def once_at(self, run_at: Union[datetime, str]) -> 'TaskBuilder':
        """
        Set a one-time execution schedule.

        Args:
            run_at: Datetime or ISO format string
        """
        if isinstance(run_at, str):
            run_at = datetime.fromisoformat(run_at)
        self.schedule = OnceSchedule(run_at)
        return self

    def with_retries(
        self,
        max_retries: int = 3,
        delay: int = 60,
        exponential: bool = True,
        backoff_factor: float = 2.0
    ) -> 'TaskBuilder':
        """Configure retry policy."""
        self.retry_policy = RetryPolicy(
            max_retries=max_retries,
            retry_delay=delay,
            exponential_backoff=exponential,
            backoff_factor=backoff_factor
        )
        return self

    def on_success(self, callback: Callable) -> 'TaskBuilder':
        """Set success callback."""
        self.on_success_callback = callback
        return self

    def on_error(self, callback: Callable) -> 'TaskBuilder':
        """Set error/failure callback."""
        self.on_failure_callback = callback
        return self

    def on_failure(self, callback: Callable) -> 'TaskBuilder':
        """Alias for on_error."""
        return self.on_error(callback)

    def with_metadata(self, **metadata) -> 'TaskBuilder':
        """Add metadata to the task."""
        self.metadata.update(metadata)
        return self

    def depends_on_task(self, task: Union[ScheduledTask, str]) -> 'TaskBuilder':
        """Add a task dependency."""
        if isinstance(task, str):
            # Look up task by ID or name
            found_task = self.scheduler.get_task(task)
            if not found_task:
                found_task = self.scheduler.get_task_by_name(task)
            if not found_task:
                raise ValueError(f"Task '{task}' not found")
            task = found_task
        self.depends_on.append(task)
        return self

    def with_priority(self, priority: int) -> 'TaskBuilder':
        """Set task priority (higher values run first)."""
        self.priority = priority
        return self

    def with_max_runs(self, max_runs: int) -> 'TaskBuilder':
        """Set maximum number of executions."""
        self.max_runs = max_runs
        return self

    def disabled(self) -> 'TaskBuilder':
        """Create task in disabled state."""
        self.enabled = False
        return self

    def build(self) -> ScheduledTask:
        """Build the task without adding it to scheduler."""
        if not self.name:
            raise ValueError("Task name is required")
        if not self.callable_obj:
            raise ValueError("Callable is required")
        if not self.schedule:
            raise ValueError("Schedule is required")

        # Wrap callable with args if provided
        if self.args or self.kwargs:
            if isinstance(self.callable_obj, CallableWrapper):
                # Already wrapped, create new wrapper with args
                func = self.callable_obj.func
            else:
                func = self.callable_obj
            self.callable_obj = CallableWrapper(func, *self.args, **self.kwargs)

        task = ScheduledTask(
            name=self.name,
            callable_obj=self.callable_obj,
            schedule=self.schedule,
            enabled=self.enabled,
            max_runs=self.max_runs,
            retry_policy=self.retry_policy,
            on_success=self.on_success_callback,
            on_failure=self.on_failure_callback,
            metadata=self.metadata,
            depends_on=self.depends_on,
            priority=self.priority
        )

        self._task = task
        return task

    def start(self) -> ScheduledTask:
        """Build and add the task to the scheduler."""
        task = self.build()

        # Add to scheduler
        self.scheduler.tasks[task.id] = task

        # Start scheduler if not running
        if not self.scheduler._running:
            self.scheduler.start()

        return task

    def start_immediately(self) -> ScheduledTask:
        """Build, add to scheduler, and execute immediately."""
        task = self.start()

        # Execute immediately
        self.scheduler.execute_now(task.id)

        return task


def add_task(scheduler: TaskScheduler) -> TaskBuilder:
    """
    Create a new TaskBuilder for the scheduler.

    This is a convenience function that can be added as a method to TaskScheduler.
    """
    return TaskBuilder(scheduler)


# Add the builder method to TaskScheduler
TaskScheduler.add_task_builder = lambda self: TaskBuilder(self)