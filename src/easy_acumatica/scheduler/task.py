"""Scheduled task implementation."""

import uuid
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Dict, List, Union
from enum import Enum

from ..batch import CallableWrapper
from .schedules import Schedule

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class RetryPolicy:
    """Retry policy for failed tasks."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: int = 60,
        exponential_backoff: bool = True,
        backoff_factor: float = 2.0
    ):
        """
        Initialize retry policy.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            exponential_backoff: Whether to use exponential backoff
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.backoff_factor = backoff_factor

    def get_retry_delay(self, attempt: int) -> int:
        """Calculate delay for given retry attempt."""
        if not self.exponential_backoff:
            return self.retry_delay

        return int(self.retry_delay * (self.backoff_factor ** (attempt - 1)))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'exponential_backoff': self.exponential_backoff,
            'backoff_factor': self.backoff_factor
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetryPolicy':
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    task_name: str
    start_time: datetime
    end_time: datetime
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'success': self.success,
            'result': str(self.result) if self.result else None,
            'error': str(self.error) if self.error else None,
            'execution_time': self.execution_time,
            'retry_count': self.retry_count
        }


class ScheduledTask:
    """Represents a scheduled task."""

    def __init__(
        self,
        name: str,
        callable_obj: Union[Callable, CallableWrapper],
        schedule: Schedule,
        task_id: Optional[str] = None,
        enabled: bool = True,
        max_runs: Optional[int] = None,
        retry_policy: Optional[RetryPolicy] = None,
        on_success: Optional[Callable[[TaskResult], None]] = None,
        on_failure: Optional[Callable[[TaskResult], None]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List['ScheduledTask']] = None,
        priority: int = 0
    ):
        """
        Initialize scheduled task.

        Args:
            name: Human-readable task name
            callable_obj: Function or CallableWrapper to execute
            schedule: Schedule object defining when to run
            task_id: Unique identifier (generated if not provided)
            enabled: Whether task is enabled
            max_runs: Maximum number of executions (None for unlimited)
            retry_policy: Policy for retrying failed tasks
            on_success: Callback for successful execution
            on_failure: Callback for failed execution
            metadata: Optional metadata dictionary
            depends_on: List of tasks this task depends on
            priority: Task priority (higher runs first)
        """
        self.id = task_id or str(uuid.uuid4())
        self.name = name
        self.schedule = schedule
        self.enabled = enabled
        self.max_runs = max_runs
        self.retry_policy = retry_policy or RetryPolicy(max_retries=0)
        self.on_success = on_success
        self.on_failure = on_failure
        self.metadata = metadata or {}
        self.depends_on = depends_on or []
        self.priority = priority

        # Wrap callable if not already wrapped
        if isinstance(callable_obj, CallableWrapper):
            self.callable = callable_obj
        else:
            self.callable = CallableWrapper(callable_obj)

        # Execution tracking
        self.status = TaskStatus.PENDING
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count: int = 0
        self.error_count: int = 0
        self.retry_count: int = 0
        self.last_result: Optional[TaskResult] = None
        self.history: List[TaskResult] = []

        # Update next run time
        self.update_next_run()

    def update_next_run(self):
        """Update the next scheduled run time."""
        if not self.enabled:
            self.next_run = None
            return

        if self.max_runs and self.run_count >= self.max_runs:
            self.next_run = None
            return

        self.next_run = self.schedule.get_next_run_time(self.last_run)

    def is_due(self) -> bool:
        """Check if task is due to run."""
        if not self.enabled or self.status == TaskStatus.RUNNING:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        # Check dependencies
        if self.depends_on:
            for dep_task in self.depends_on:
                if dep_task.status != TaskStatus.COMPLETED:
                    return False

        return self.schedule.is_due(self.last_run)

    def can_retry(self) -> bool:
        """Check if task can be retried after failure."""
        return self.retry_count < self.retry_policy.max_retries

    def get_retry_delay(self) -> int:
        """Get delay before next retry."""
        return self.retry_policy.get_retry_delay(self.retry_count)

    def execute(self) -> TaskResult:
        """Execute the task."""
        start_time = datetime.now()
        self.status = TaskStatus.RUNNING

        logger.info(f"Executing task '{self.name}' (ID: {self.id})")

        try:
            # Execute the callable
            result = self.callable.execute()

            # Task succeeded
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            task_result = TaskResult(
                task_id=self.id,
                task_name=self.name,
                start_time=start_time,
                end_time=end_time,
                success=True,
                result=result,
                execution_time=execution_time,
                retry_count=self.retry_count
            )

            # Update task state
            self.status = TaskStatus.COMPLETED
            self.last_run = end_time
            self.run_count += 1
            self.retry_count = 0
            self.last_result = task_result
            self.history.append(task_result)

            # Call success callback
            if self.on_success:
                try:
                    self.on_success(task_result)
                except Exception as e:
                    logger.error(f"Error in success callback for task '{self.name}': {e}")

            # Update next run time
            self.update_next_run()

            logger.info(f"Task '{self.name}' completed successfully in {execution_time:.2f}s")
            return task_result

        except Exception as e:
            # Task failed
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            task_result = TaskResult(
                task_id=self.id,
                task_name=self.name,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error=e,
                execution_time=execution_time,
                retry_count=self.retry_count
            )

            # Update task state
            self.status = TaskStatus.FAILED
            self.error_count += 1
            self.last_result = task_result
            self.history.append(task_result)

            logger.error(f"Task '{self.name}' failed: {e}")

            # Handle retry
            if self.can_retry():
                self.retry_count += 1
                self.status = TaskStatus.PENDING
                logger.info(f"Task '{self.name}' will retry (attempt {self.retry_count}/{self.retry_policy.max_retries})")
            else:
                # Call failure callback
                if self.on_failure:
                    try:
                        self.on_failure(task_result)
                    except Exception as cb_error:
                        logger.error(f"Error in failure callback for task '{self.name}': {cb_error}")

                # Update next run time for next scheduled execution
                self.last_run = end_time
                self.run_count += 1
                self.retry_count = 0
                self.update_next_run()

            return task_result

    def pause(self):
        """Pause the task."""
        self.enabled = False
        self.status = TaskStatus.PAUSED
        self.next_run = None
        logger.info(f"Task '{self.name}' paused")

    def resume(self):
        """Resume the task."""
        self.enabled = True
        self.status = TaskStatus.PENDING
        self.update_next_run()
        logger.info(f"Task '{self.name}' resumed")

    def cancel(self):
        """Cancel the task."""
        self.enabled = False
        self.status = TaskStatus.CANCELLED
        self.next_run = None
        logger.info(f"Task '{self.name}' cancelled")

    def reset(self):
        """Reset task execution state."""
        self.status = TaskStatus.PENDING
        self.last_run = None
        self.run_count = 0
        self.error_count = 0
        self.retry_count = 0
        self.last_result = None
        self.history.clear()
        self.update_next_run()
        logger.info(f"Task '{self.name}' reset")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'schedule': self.schedule.to_dict(),
            'enabled': self.enabled,
            'max_runs': self.max_runs,
            'retry_policy': self.retry_policy.to_dict() if self.retry_policy else None,
            'metadata': self.metadata,
            'priority': self.priority,
            'status': self.status.value,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'error_count': self.error_count,
            'retry_count': self.retry_count
        }

    def __repr__(self) -> str:
        status = f"enabled" if self.enabled else "disabled"
        return f"ScheduledTask('{self.name}', {self.schedule}, {status}, runs={self.run_count})"