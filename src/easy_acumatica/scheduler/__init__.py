"""Task scheduler module for Easy-Acumatica."""

from .core import TaskScheduler
from .task import ScheduledTask, TaskResult, TaskStatus, RetryPolicy
from .schedules import (
    Schedule,
    IntervalSchedule,
    CronSchedule,
    OnceSchedule,
    DailySchedule,
    WeeklySchedule,
    deserialize_schedule
)
from .decorators import schedule, every, daily, weekly, cron, set_global_scheduler, get_global_scheduler
from .builder import TaskBuilder
from .persistence import TaskPersistence
from .utils import (
    parse_time_string,
    resolve_task_dependencies,
    calculate_next_run_times,
    format_schedule_summary,
    estimate_resource_usage,
    TaskMonitor
)

__all__ = [
    # Core
    'TaskScheduler',
    'ScheduledTask',
    'TaskResult',
    'TaskStatus',
    'RetryPolicy',
    # Schedules
    'Schedule',
    'IntervalSchedule',
    'CronSchedule',
    'OnceSchedule',
    'DailySchedule',
    'WeeklySchedule',
    'deserialize_schedule',
    # Decorators
    'schedule',
    'every',
    'daily',
    'weekly',
    'cron',
    'set_global_scheduler',
    'get_global_scheduler',
    # Builder
    'TaskBuilder',
    # Persistence
    'TaskPersistence',
    # Utils
    'parse_time_string',
    'resolve_task_dependencies',
    'calculate_next_run_times',
    'format_schedule_summary',
    'estimate_resource_usage',
    'TaskMonitor'
]