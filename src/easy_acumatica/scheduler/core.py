"""Core task scheduler implementation."""

import logging
import sys
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable, Union, Any
from concurrent.futures import ThreadPoolExecutor, Future
import json
from pathlib import Path

from .task import ScheduledTask, TaskResult, TaskStatus
from .schedules import Schedule, deserialize_schedule
from ..batch import CallableWrapper

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Main task scheduler that manages and executes scheduled tasks."""

    def __init__(
        self,
        client: Optional[Any] = None,  # Type hint as Any to avoid circular import
        max_workers: int = 5,
        check_interval: int = 1,
        persist_tasks: bool = False,
        persist_file: Optional[Path] = None
    ):
        """
        Initialize task scheduler.

        Args:
            client: AcumaticaClient instance (optional)
            max_workers: Maximum concurrent task executions
            check_interval: Interval in seconds to check for due tasks
            persist_tasks: Whether to persist tasks to disk
            persist_file: Path to persistence file
        """
        self.client = client
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.persist_tasks = persist_tasks
        self.persist_file = persist_file or Path.home() / '.easy_acumatica' / 'scheduled_tasks.json'

        # Task management
        self.tasks: Dict[str, ScheduledTask] = {}
        self._task_lock = threading.RLock()

        # Execution management
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running_tasks: Dict[str, Future] = {}
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.start_time: Optional[datetime] = None

        # Persisted-task metadata loaded from disk that has no associated
        # callable yet. Keyed by task_id; populated by load_tasks(). Users
        # rehydrate via restore_task(task_id, callable_obj).
        self.pending_restorations: Dict[str, Dict[str, Any]] = {}

        # Load persisted tasks if enabled
        if self.persist_tasks:
            self.load_tasks()

    def add_task(
        self,
        name: str,
        callable_obj: Union[Callable, CallableWrapper],
        schedule: Schedule,
        **kwargs
    ) -> ScheduledTask:
        """
        Add a new scheduled task.

        Args:
            name: Task name
            callable_obj: Function or CallableWrapper to execute
            schedule: Schedule object
            **kwargs: Additional arguments for ScheduledTask

        Returns:
            The created ScheduledTask
        """
        with self._task_lock:
            # Check for duplicate names
            if name in [task.name for task in self.tasks.values()]:
                raise ValueError(f"Task with name '{name}' already exists")

            task = ScheduledTask(name, callable_obj, schedule, **kwargs)
            self.tasks[task.id] = task

            logger.info(f"Added task '{name}' (ID: {task.id}) with schedule {schedule}")

            if self.persist_tasks:
                self.save_tasks()

            return task

    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task by ID.

        Args:
            task_id: Task ID to remove

        Returns:
            True if removed, False if not found
        """
        with self._task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.cancel()
                del self.tasks[task_id]

                logger.info(f"Removed task '{task.name}' (ID: {task_id})")

                if self.persist_tasks:
                    self.save_tasks()

                return True
            return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_task_by_name(self, name: str) -> Optional[ScheduledTask]:
        """Get a task by name."""
        for task in self.tasks.values():
            if task.name == name:
                return task
        return None

    def list_tasks(self) -> List[ScheduledTask]:
        """Get list of all tasks."""
        return list(self.tasks.values())

    def pause_task(self, task_id: str) -> bool:
        """Pause a task."""
        task = self.get_task(task_id)
        if task:
            task.pause()
            if self.persist_tasks:
                self.save_tasks()
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        task = self.get_task(task_id)
        if task:
            task.resume()
            if self.persist_tasks:
                self.save_tasks()
            return True
        return False

    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        # The previous executor was shut down by stop(); allocate a fresh
        # one so submits don't fail with "cannot schedule new futures
        # after shutdown".
        if self._executor is None or getattr(self._executor, '_shutdown', False):
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        self._running = True
        self._stop_event.clear()
        self.start_time = datetime.now()

        # Start scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="TaskScheduler"
        )
        self._scheduler_thread.start()

        logger.info(f"Scheduler started with {len(self.tasks)} tasks")

    def stop(self, wait: bool = True, timeout: Optional[float] = None):
        """
        Stop the scheduler.

        Args:
            wait: Whether to wait for running tasks to complete
            timeout: Maximum time to wait for tasks to complete
        """
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping scheduler...")
        self._running = False
        self._stop_event.set()

        # Wait for scheduler thread to stop
        if self._scheduler_thread and wait:
            self._scheduler_thread.join(timeout=timeout)

        # Shutdown executor. ``cancel_futures`` is Python 3.9+ only.
        if self._executor is not None:
            if sys.version_info >= (3, 9):
                self._executor.shutdown(wait=wait, cancel_futures=not wait)
            else:
                self._executor.shutdown(wait=wait)

        # Save tasks if persistence is enabled
        if self.persist_tasks:
            self.save_tasks()

        logger.info("Scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop that checks for due tasks."""
        logger.debug("Scheduler loop started")

        while self._running and not self._stop_event.is_set():
            try:
                self._check_and_execute_due_tasks()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Wait for next check interval
            self._stop_event.wait(self.check_interval)

        logger.debug("Scheduler loop ended")

    def _check_and_execute_due_tasks(self):
        """Check for due tasks and execute them."""
        with self._task_lock:
            due_tasks = []

            # Find all due tasks
            for task in self.tasks.values():
                if task.is_due():
                    due_tasks.append(task)

            # Sort by priority (higher priority first)
            due_tasks.sort(key=lambda t: t.priority, reverse=True)

            # Execute due tasks
            for task in due_tasks:
                # Skip if already running
                if task.id in self._running_tasks:
                    continue

                # Submit task for execution
                future = self._executor.submit(self._execute_task, task)
                self._running_tasks[task.id] = future

                # Add callback to clean up running tasks
                future.add_done_callback(
                    lambda f, tid=task.id: self._task_completed(tid, f)
                )

    def _execute_task(self, task: ScheduledTask) -> TaskResult:
        """Execute a single task."""
        try:
            result = task.execute()
            self.total_executions += 1

            if result.success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            # Save tasks if persistence is enabled
            if self.persist_tasks:
                self.save_tasks()

            return result

        except Exception as e:
            logger.error(f"Unexpected error executing task '{task.name}': {e}")
            self.failed_executions += 1
            raise

    def _task_completed(self, task_id: str, future: Future):
        """Callback when task execution completes.

        Retry scheduling lives on the ScheduledTask itself (it sets
        ``_retry_after``); the scheduler loop will pick the task up again
        once that deadline passes. We deliberately don't spawn a Timer
        here - that previously raced with ``_check_and_execute_due_tasks``
        and could fire the same task twice.
        """
        with self._task_lock:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            try:
                future.result()  # surface any unexpected exception via logging
            except Exception as e:
                logger.error(f"Error handling task completion for {task_id}: {e}")

    def execute_now(self, task_id: str) -> Optional[Future]:
        """
        Execute a task immediately, regardless of schedule.

        Args:
            task_id: Task ID to execute

        Returns:
            Future object for the execution, or None if task not found
        """
        task = self.get_task(task_id)
        if not task:
            return None

        # Lazily allocate the executor so callers can fire tasks before
        # start() (or after stop()).
        if self._executor is None or getattr(self._executor, '_shutdown', False):
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        return self._executor.submit(self._execute_task, task)

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'running': self._running,
            'uptime_seconds': uptime,
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'running_tasks': len(self._running_tasks),
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': (
                self.successful_executions / self.total_executions
                if self.total_executions > 0 else 0
            )
        }

    def save_tasks(self):
        """Save tasks to persistence file."""
        if not self.persist_file:
            return

        try:
            # Create directory if it doesn't exist
            self.persist_file.parent.mkdir(parents=True, exist_ok=True)

            # Serialize tasks
            tasks_data = {}
            for task_id, task in self.tasks.items():
                # We can only persist the schedule and metadata,
                # not the actual callable
                tasks_data[task_id] = {
                    'name': task.name,
                    'schedule': task.schedule.to_dict(),
                    'enabled': task.enabled,
                    'max_runs': task.max_runs,
                    'metadata': task.metadata,
                    'priority': task.priority,
                    'run_count': task.run_count,
                    'last_run': task.last_run.isoformat() if task.last_run else None
                }

            # Write to file
            with open(self.persist_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)

            logger.debug(f"Saved {len(tasks_data)} tasks to {self.persist_file}")

        except Exception as e:
            logger.error(f"Error saving tasks: {e}")

    def load_tasks(self):
        """Load persisted task metadata from disk.

        Callables are not serializable, so this populates
        ``self.pending_restorations`` (a dict of task_id -> metadata) for
        the caller to rehydrate via :meth:`restore_task`. Schedules are
        deserialized eagerly so the caller can inspect them before
        rebuilding.
        """
        if not self.persist_file or not self.persist_file.exists():
            return

        try:
            with open(self.persist_file, 'r') as f:
                tasks_data = json.load(f)

            logger.info(f"Loading {len(tasks_data)} tasks from {self.persist_file}")

            for task_id, task_data in tasks_data.items():
                try:
                    schedule = deserialize_schedule(task_data['schedule'])
                except Exception as e:
                    logger.error(
                        f"Skipping task '{task_data.get('name')}': bad schedule ({e})"
                    )
                    continue
                last_run_raw = task_data.get('last_run')
                last_run = (
                    datetime.fromisoformat(last_run_raw) if last_run_raw else None
                )
                self.pending_restorations[task_id] = {
                    'name': task_data['name'],
                    'schedule': schedule,
                    'enabled': task_data.get('enabled', True),
                    'max_runs': task_data.get('max_runs'),
                    'metadata': task_data.get('metadata', {}),
                    'priority': task_data.get('priority', 0),
                    'run_count': task_data.get('run_count', 0),
                    'last_run': last_run,
                }
            if self.pending_restorations:
                logger.info(
                    f"{len(self.pending_restorations)} task(s) awaiting "
                    f"restore_task() to attach a callable."
                )

        except Exception as e:
            logger.error(f"Error loading tasks: {e}")

    def restore_task(
        self,
        task_id: str,
        callable_obj: Union[Callable, CallableWrapper],
    ) -> Optional[ScheduledTask]:
        """Rehydrate a persisted task by attaching a callable.

        Returns the new :class:`ScheduledTask`, or ``None`` if the id
        wasn't in :attr:`pending_restorations`.
        """
        meta = self.pending_restorations.pop(task_id, None)
        if meta is None:
            return None
        task = self.add_task(
            name=meta['name'],
            callable_obj=callable_obj,
            schedule=meta['schedule'],
            task_id=task_id,
            enabled=meta['enabled'],
            max_runs=meta['max_runs'],
            metadata=meta['metadata'],
            priority=meta['priority'],
        )
        # Restore execution counters so persistence is round-trip lossless.
        task.run_count = meta.get('run_count', 0)
        task.last_run = meta.get('last_run')
        task.update_next_run()
        return task

    def clear_history(self, task_id: Optional[str] = None):
        """
        Clear execution history.

        Args:
            task_id: Clear history for specific task, or all tasks if None
        """
        if task_id:
            task = self.get_task(task_id)
            if task:
                task.history.clear()
        else:
            for task in self.tasks.values():
                task.history.clear()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"TaskScheduler({status}, tasks={len(self.tasks)}, workers={self.max_workers})"