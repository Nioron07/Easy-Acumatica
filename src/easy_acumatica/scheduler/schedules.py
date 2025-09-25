"""Schedule types for the task scheduler."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import re


class Schedule(ABC):
    """Abstract base class for all schedule types."""

    @abstractmethod
    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate the next run time based on the schedule."""
        pass

    @abstractmethod
    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if the task is due to run."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize schedule to dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Deserialize schedule from dictionary."""
        pass


class IntervalSchedule(Schedule):
    """Schedule that runs at fixed intervals."""

    def __init__(
        self,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        weeks: int = 0
    ):
        """
        Initialize interval schedule.

        Args:
            seconds: Number of seconds between runs
            minutes: Number of minutes between runs
            hours: Number of hours between runs
            days: Number of days between runs
            weeks: Number of weeks between runs
        """
        self.interval = timedelta(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
            weeks=weeks
        )

        if self.interval.total_seconds() <= 0:
            raise ValueError("Interval must be positive")

    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate next run time by adding interval to last run or now."""
        if last_run is None:
            return datetime.now()
        return last_run + self.interval

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if enough time has passed since last run."""
        if last_run is None:
            return True
        return datetime.now() >= last_run + self.interval

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': 'interval',
            'seconds': int(self.interval.total_seconds())
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntervalSchedule':
        """Deserialize from dictionary."""
        return cls(seconds=data['seconds'])

    def __repr__(self) -> str:
        total_seconds = int(self.interval.total_seconds())
        if total_seconds < 60:
            return f"IntervalSchedule(every {total_seconds} seconds)"
        elif total_seconds < 3600:
            return f"IntervalSchedule(every {total_seconds // 60} minutes)"
        elif total_seconds < 86400:
            return f"IntervalSchedule(every {total_seconds // 3600} hours)"
        else:
            return f"IntervalSchedule(every {total_seconds // 86400} days)"


class CronSchedule(Schedule):
    """Schedule based on cron expressions."""

    def __init__(self, expression: str):
        """
        Initialize cron schedule.

        Args:
            expression: Cron expression string (e.g., "0 9 * * MON-FRI")
        """
        self.expression = expression
        self._validate_expression()

        # Import croniter only when CronSchedule is used
        try:
            from croniter import croniter
            self._croniter_available = True
        except ImportError:
            self._croniter_available = False
            import warnings
            warnings.warn(
                "croniter library not installed. CronSchedule will use simple parsing. "
                "Install with: pip install croniter"
            )

    def _validate_expression(self):
        """Basic validation of cron expression format."""
        parts = self.expression.split()
        if len(parts) < 5:
            raise ValueError(f"Invalid cron expression: {self.expression}")

    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate next run time based on cron expression."""
        base_time = last_run or datetime.now()

        if self._croniter_available:
            from croniter import croniter
            cron = croniter(self.expression, base_time)
            return cron.get_next(datetime)
        else:
            # Fallback to simple daily schedule if croniter not available
            # This is a simplified implementation
            return base_time + timedelta(days=1)

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if current time matches cron expression."""
        if last_run is None:
            return True

        next_run = self.get_next_run_time(last_run)
        return datetime.now() >= next_run

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': 'cron',
            'expression': self.expression
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CronSchedule':
        """Deserialize from dictionary."""
        return cls(expression=data['expression'])

    def __repr__(self) -> str:
        return f"CronSchedule('{self.expression}')"


class OnceSchedule(Schedule):
    """Schedule that runs once at a specific time."""

    def __init__(self, run_at: datetime):
        """
        Initialize one-time schedule.

        Args:
            run_at: Datetime when the task should run
        """
        self.run_at = run_at
        self._executed = False

    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Return the scheduled time if not yet executed."""
        if self._executed or (last_run and last_run >= self.run_at):
            return None
        return self.run_at

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if current time is past scheduled time."""
        if self._executed or (last_run and last_run >= self.run_at):
            return False
        return datetime.now() >= self.run_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': 'once',
            'run_at': self.run_at.isoformat(),
            'executed': self._executed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OnceSchedule':
        """Deserialize from dictionary."""
        schedule = cls(run_at=datetime.fromisoformat(data['run_at']))
        schedule._executed = data.get('executed', False)
        return schedule

    def __repr__(self) -> str:
        return f"OnceSchedule(at {self.run_at.strftime('%Y-%m-%d %H:%M:%S')})"


class DailySchedule(Schedule):
    """Schedule that runs daily at specific time(s)."""

    def __init__(self, hour: int, minute: int = 0, second: int = 0):
        """
        Initialize daily schedule.

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
            second: Second of minute (0-59)
        """
        if not 0 <= hour <= 23:
            raise ValueError("Hour must be between 0 and 23")
        if not 0 <= minute <= 59:
            raise ValueError("Minute must be between 0 and 59")
        if not 0 <= second <= 59:
            raise ValueError("Second must be between 0 and 59")

        self.hour = hour
        self.minute = minute
        self.second = second

    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate next daily run time."""
        now = datetime.now()
        next_run = now.replace(hour=self.hour, minute=self.minute, second=self.second, microsecond=0)

        # If time has passed today, schedule for tomorrow
        if next_run <= now or (last_run and next_run <= last_run):
            next_run += timedelta(days=1)

        return next_run

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if it's time for daily run."""
        now = datetime.now()
        scheduled_time = now.replace(hour=self.hour, minute=self.minute, second=self.second, microsecond=0)

        # Check if we're past the scheduled time
        if now < scheduled_time:
            return False

        # Check if we've already run today
        if last_run:
            if last_run.date() == now.date():
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': 'daily',
            'hour': self.hour,
            'minute': self.minute,
            'second': self.second
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailySchedule':
        """Deserialize from dictionary."""
        return cls(
            hour=data['hour'],
            minute=data.get('minute', 0),
            second=data.get('second', 0)
        )

    def __repr__(self) -> str:
        return f"DailySchedule(at {self.hour:02d}:{self.minute:02d}:{self.second:02d})"


class WeeklySchedule(Schedule):
    """Schedule that runs weekly on specific day(s)."""

    WEEKDAYS = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
        'fri': 4, 'sat': 5, 'sun': 6
    }

    def __init__(self, weekday: Union[str, int], hour: int, minute: int = 0):
        """
        Initialize weekly schedule.

        Args:
            weekday: Day of week (0=Monday, 6=Sunday) or name
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
        """
        if isinstance(weekday, str):
            weekday = self.WEEKDAYS.get(weekday.lower())
            if weekday is None:
                raise ValueError(f"Invalid weekday: {weekday}")

        if not 0 <= weekday <= 6:
            raise ValueError("Weekday must be between 0 and 6")
        if not 0 <= hour <= 23:
            raise ValueError("Hour must be between 0 and 23")
        if not 0 <= minute <= 59:
            raise ValueError("Minute must be between 0 and 59")

        self.weekday = weekday
        self.hour = hour
        self.minute = minute

    def get_next_run_time(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate next weekly run time."""
        now = datetime.now()
        days_ahead = self.weekday - now.weekday()

        if days_ahead < 0:  # Target day already happened this week
            days_ahead += 7
        elif days_ahead == 0:  # Target day is today
            scheduled_time = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            if scheduled_time <= now or (last_run and scheduled_time <= last_run):
                days_ahead = 7  # Schedule for next week

        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)

        return next_run

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if it's time for weekly run."""
        now = datetime.now()

        # Check if it's the right day and time
        if now.weekday() != self.weekday:
            return False

        scheduled_time = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if now < scheduled_time:
            return False

        # Check if we've already run this week
        if last_run:
            # Calculate start of current week
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

            if last_run >= start_of_week:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': 'weekly',
            'weekday': self.weekday,
            'hour': self.hour,
            'minute': self.minute
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklySchedule':
        """Deserialize from dictionary."""
        return cls(
            weekday=data['weekday'],
            hour=data['hour'],
            minute=data.get('minute', 0)
        )

    def __repr__(self) -> str:
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"WeeklySchedule({day_names[self.weekday]} at {self.hour:02d}:{self.minute:02d})"


# Schedule type registry for deserialization
SCHEDULE_TYPES = {
    'interval': IntervalSchedule,
    'cron': CronSchedule,
    'once': OnceSchedule,
    'daily': DailySchedule,
    'weekly': WeeklySchedule
}


def deserialize_schedule(data: Dict[str, Any]) -> Schedule:
    """Deserialize a schedule from dictionary."""
    schedule_type = data.get('type')
    if schedule_type not in SCHEDULE_TYPES:
        raise ValueError(f"Unknown schedule type: {schedule_type}")

    schedule_class = SCHEDULE_TYPES[schedule_type]
    return schedule_class.from_dict(data)