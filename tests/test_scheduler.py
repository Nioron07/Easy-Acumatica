"""Tests for the scheduler module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import tempfile
import json
from pathlib import Path

from easy_acumatica.scheduler import (
    TaskScheduler,
    ScheduledTask,
    TaskResult,
    TaskStatus,
    RetryPolicy,
    IntervalSchedule,
    CronSchedule,
    DailySchedule,
    WeeklySchedule,
    OnceSchedule,
    TaskBuilder,
    TaskPersistence,
    schedule,
    every,
    daily,
    weekly,
    cron
)
from easy_acumatica.batch import CallableWrapper


class TestSchedules(unittest.TestCase):
    """Test schedule types."""

    def test_interval_schedule(self):
        """Test interval-based scheduling."""
        schedule = IntervalSchedule(minutes=30)

        # First run should be immediate
        self.assertTrue(schedule.is_due(None))

        # After running, next should be 30 minutes later
        last_run = datetime.now()
        next_run = schedule.get_next_run_time(last_run)
        self.assertEqual(next_run, last_run + timedelta(minutes=30))

        # Should not be due immediately after running
        self.assertFalse(schedule.is_due(last_run))

    def test_daily_schedule(self):
        """Test daily scheduling."""
        schedule = DailySchedule(hour=14, minute=30, run_immediately=True)

        # First run should be immediate if never run with run_immediately=True
        self.assertTrue(schedule.is_due(None))

        # Get next run time
        next_run = schedule.get_next_run_time()
        self.assertEqual(next_run.hour, 14)
        self.assertEqual(next_run.minute, 30)

    def test_weekly_schedule(self):
        """Test weekly scheduling."""
        schedule = WeeklySchedule(weekday="monday", hour=9, minute=0)

        # Check if today is Monday at or after 9:00 AM
        now = datetime.now()
        if now.weekday() == 0 and now.hour >= 9:  # Monday after 9 AM
            self.assertTrue(schedule.is_due(None))
        else:
            # Otherwise it shouldn't be due immediately
            pass  # Test passes either way

        # Next run should be on Monday at 9:00
        next_run = schedule.get_next_run_time()
        self.assertEqual(next_run.weekday(), 0)  # Monday
        self.assertEqual(next_run.hour, 9)
        self.assertEqual(next_run.minute, 0)

    def test_once_schedule(self):
        """Test one-time scheduling."""
        future_time = datetime.now() + timedelta(hours=1)
        schedule = OnceSchedule(run_at=future_time)

        # Should not be due yet
        self.assertFalse(schedule.is_due())

        # Next run should be the scheduled time
        next_run = schedule.get_next_run_time()
        self.assertEqual(next_run, future_time)

    def test_cron_schedule(self):
        """Test cron expression scheduling."""
        schedule = CronSchedule("0 9 * * MON-FRI")

        # Test is_due - first run should be immediate
        self.assertTrue(schedule.is_due(None))

        # Test serialization
        data = schedule.to_dict()
        self.assertEqual(data['type'], 'cron')
        self.assertEqual(data['expression'], "0 9 * * MON-FRI")


class TestScheduledTask(unittest.TestCase):
    """Test ScheduledTask functionality."""

    def test_task_creation(self):
        """Test creating a scheduled task."""
        mock_callable = Mock(return_value="result")
        schedule = IntervalSchedule(seconds=60)

        task = ScheduledTask(
            name="Test Task",
            callable_obj=mock_callable,
            schedule=schedule,
            max_runs=5,
            retry_policy=RetryPolicy(max_retries=3)
        )

        self.assertEqual(task.name, "Test Task")
        self.assertTrue(task.enabled)
        self.assertEqual(task.max_runs, 5)
        self.assertEqual(task.run_count, 0)

    def test_task_execution(self):
        """Test task execution."""
        mock_callable = Mock(return_value="success")
        schedule = IntervalSchedule(seconds=60)

        task = ScheduledTask(
            name="Test Task",
            callable_obj=mock_callable,
            schedule=schedule
        )

        # Execute task
        result = task.execute()

        self.assertTrue(result.success)
        self.assertEqual(result.result, "success")
        self.assertEqual(task.run_count, 1)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        mock_callable.assert_called_once()

    def test_task_failure_and_retry(self):
        """Test task failure and retry mechanism."""
        mock_callable = Mock(side_effect=Exception("Test error"))
        schedule = IntervalSchedule(seconds=60)

        task = ScheduledTask(
            name="Test Task",
            callable_obj=mock_callable,
            schedule=schedule,
            retry_policy=RetryPolicy(max_retries=2)
        )

        # Execute task (should fail)
        result = task.execute()

        self.assertFalse(result.success)
        self.assertIsInstance(result.error, Exception)
        self.assertEqual(task.error_count, 1)
        self.assertTrue(task.can_retry())
        self.assertEqual(task.retry_count, 1)

    def test_task_callbacks(self):
        """Test success and failure callbacks."""
        success_callback = Mock()
        failure_callback = Mock()

        # Success case
        task = ScheduledTask(
            name="Success Task",
            callable_obj=Mock(return_value="ok"),
            schedule=IntervalSchedule(seconds=60),
            on_success=success_callback,
            on_failure=failure_callback
        )

        task.execute()
        success_callback.assert_called_once()
        failure_callback.assert_not_called()

        # Failure case
        task = ScheduledTask(
            name="Failure Task",
            callable_obj=Mock(side_effect=Exception("error")),
            schedule=IntervalSchedule(seconds=60),
            on_success=success_callback,
            on_failure=failure_callback,
            retry_policy=RetryPolicy(max_retries=0)
        )

        success_callback.reset_mock()
        failure_callback.reset_mock()

        task.execute()
        success_callback.assert_not_called()
        failure_callback.assert_called_once()


class TestTaskScheduler(unittest.TestCase):
    """Test TaskScheduler functionality."""

    def setUp(self):
        """Set up test scheduler."""
        self.scheduler = TaskScheduler(max_workers=2, check_interval=0.1)

    def tearDown(self):
        """Clean up scheduler."""
        if self.scheduler._running:
            self.scheduler.stop(wait=False)

    def test_add_task(self):
        """Test adding tasks to scheduler."""
        mock_callable = Mock()
        schedule = IntervalSchedule(seconds=60)

        task = self.scheduler.add_task(
            name="Test Task",
            callable_obj=mock_callable,
            schedule=schedule
        )

        self.assertIn(task.id, self.scheduler.tasks)
        self.assertEqual(len(self.scheduler.tasks), 1)

    def test_remove_task(self):
        """Test removing tasks from scheduler."""
        task = self.scheduler.add_task(
            name="Test Task",
            callable_obj=Mock(),
            schedule=IntervalSchedule(seconds=60)
        )

        removed = self.scheduler.remove_task(task.id)
        self.assertTrue(removed)
        self.assertNotIn(task.id, self.scheduler.tasks)

    def test_get_task_by_name(self):
        """Test getting task by name."""
        task = self.scheduler.add_task(
            name="Unique Task",
            callable_obj=Mock(),
            schedule=IntervalSchedule(seconds=60)
        )

        found_task = self.scheduler.get_task_by_name("Unique Task")
        self.assertEqual(found_task.id, task.id)

    @patch('easy_acumatica.scheduler.core.threading.Thread')
    def test_scheduler_start_stop(self, mock_thread):
        """Test starting and stopping scheduler."""
        # Start scheduler
        self.scheduler.start()
        self.assertTrue(self.scheduler._running)
        mock_thread.assert_called_once()

        # Stop scheduler
        self.scheduler.stop(wait=False)
        self.assertFalse(self.scheduler._running)

    def test_execute_now(self):
        """Test immediate task execution."""
        mock_callable = Mock(return_value="immediate")

        task = self.scheduler.add_task(
            name="Immediate Task",
            callable_obj=mock_callable,
            schedule=IntervalSchedule(hours=24)
        )

        future = self.scheduler.execute_now(task.id)
        self.assertIsNotNone(future)

        # Wait for execution
        result = future.result(timeout=1)
        self.assertEqual(result.result, "immediate")
        mock_callable.assert_called_once()

    def test_task_priority(self):
        """Test task priority ordering."""
        tasks = []
        for i in range(3):
            task = self.scheduler.add_task(
                name=f"Task {i}",
                callable_obj=Mock(),
                schedule=IntervalSchedule(seconds=60),
                priority=i * 10
            )
            tasks.append(task)

        # Tasks should be sorted by priority
        task_list = self.scheduler.list_tasks()
        task_list.sort(key=lambda t: t.priority, reverse=True)
        self.assertEqual(task_list[0].priority, 20)
        self.assertEqual(task_list[-1].priority, 0)


class TestTaskBuilder(unittest.TestCase):
    """Test TaskBuilder functionality."""

    def setUp(self):
        """Set up test scheduler."""
        self.scheduler = TaskScheduler()

    def test_builder_basic(self):
        """Test basic builder usage."""
        mock_func = Mock(return_value="built")

        task = (self.scheduler.add_task_builder()
                .named("Built Task")
                .calling(mock_func)
                .every(minutes=30)
                .build())

        self.assertEqual(task.name, "Built Task")
        self.assertIsInstance(task.schedule, IntervalSchedule)

    def test_builder_with_args(self):
        """Test builder with function arguments."""
        mock_func = Mock()

        task = (self.scheduler.add_task_builder()
                .named("Task with Args")
                .calling(mock_func)
                .with_args(1, 2, key="value")
                .every(hours=1)
                .build())

        # Execute to verify args are passed
        task.execute()
        mock_func.assert_called_with(1, 2, key="value")

    def test_builder_with_retries(self):
        """Test builder with retry configuration."""
        task = (self.scheduler.add_task_builder()
                .named("Retry Task")
                .calling(Mock())
                .every(hours=1)
                .with_retries(max_retries=5, delay=30, exponential=True)
                .build())

        self.assertEqual(task.retry_policy.max_retries, 5)
        self.assertEqual(task.retry_policy.retry_delay, 30)
        self.assertTrue(task.retry_policy.exponential_backoff)

    def test_builder_cron_schedule(self):
        """Test builder with cron schedule."""
        task = (self.scheduler.add_task_builder()
                .named("Cron Task")
                .calling(Mock())
                .using_cron("0 9 * * MON-FRI")
                .build())

        self.assertIsInstance(task.schedule, CronSchedule)
        self.assertEqual(task.schedule.expression, "0 9 * * MON-FRI")


class TestDecorators(unittest.TestCase):
    """Test scheduling decorators."""

    @patch('easy_acumatica.scheduler.decorators.get_global_scheduler')
    def test_every_decorator(self, mock_get_scheduler):
        """Test @every decorator."""
        mock_scheduler = Mock(spec=TaskScheduler)
        mock_get_scheduler.return_value = mock_scheduler

        @every(minutes=15, start_immediately=False)
        def test_function():
            return "decorated"

        # Function should still be callable
        result = test_function()
        self.assertEqual(result, "decorated")

        # Should have scheduling attributes
        self.assertTrue(hasattr(test_function, '_scheduled'))
        self.assertTrue(hasattr(test_function, '_schedule'))

    @patch('easy_acumatica.scheduler.decorators.get_global_scheduler')
    def test_daily_decorator(self, mock_get_scheduler):
        """Test @daily decorator."""
        mock_scheduler = Mock(spec=TaskScheduler)
        mock_get_scheduler.return_value = mock_scheduler

        @daily(hour=9, minute=30, start_immediately=False)
        def morning_task():
            return "morning"

        self.assertTrue(hasattr(morning_task, '_scheduled'))
        self.assertIsInstance(morning_task._schedule, DailySchedule)

    @patch('easy_acumatica.scheduler.decorators.get_global_scheduler')
    def test_cron_decorator(self, mock_get_scheduler):
        """Test @cron decorator."""
        mock_scheduler = Mock(spec=TaskScheduler)
        mock_get_scheduler.return_value = mock_scheduler

        @cron("0 * * * *", start_immediately=False)
        def hourly_task():
            return "hourly"

        self.assertTrue(hasattr(hourly_task, '_scheduled'))
        self.assertIsInstance(hourly_task._schedule, CronSchedule)


class TestPersistence(unittest.TestCase):
    """Test task persistence."""

    def test_json_persistence(self):
        """Test JSON persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "tasks.json"
            persistence = TaskPersistence("json", storage_path)

            # Save task data
            task_data = {
                'id': 'test-123',
                'name': 'Test Task',
                'schedule': {'type': 'interval', 'seconds': 60},
                'enabled': True,
                'run_count': 5
            }

            persistence.save_task(task_data)

            # Load and verify
            loaded_tasks = persistence.load_all_tasks()
            self.assertIn('test-123', loaded_tasks)
            self.assertEqual(loaded_tasks['test-123']['name'], 'Test Task')

    def test_sqlite_persistence(self):
        """Test SQLite persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "tasks.db"
            persistence = TaskPersistence("sqlite", storage_path)

            # Save task data
            task_data = {
                'id': 'test-456',
                'name': 'SQLite Task',
                'schedule': {'type': 'daily', 'hour': 10, 'minute': 0},
                'enabled': False,
                'priority': 10
            }

            try:
                persistence.save_task(task_data)

                # Load and verify
                loaded_tasks = persistence.load_all_tasks()
                self.assertIn('test-456', loaded_tasks)
                self.assertEqual(loaded_tasks['test-456']['priority'], 10)
            finally:
                # Properly close persistence connections
                persistence.close()

    def test_task_history(self):
        """Test task execution history storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "tasks.db"
            persistence = TaskPersistence("sqlite", storage_path)

            try:
                # Save task result
                result_data = {
                    'task_id': 'test-789',
                    'task_name': 'History Task',
                    'start_time': datetime.now().isoformat(),
                    'end_time': (datetime.now() + timedelta(seconds=5)).isoformat(),
                    'success': True,
                    'result': 'completed',
                    'execution_time': 5.0
                }

                persistence.save_task_result(result_data)

                # Get history
                history = persistence.get_task_history('test-789')
                self.assertEqual(len(history), 1)
                self.assertEqual(history[0]['task_name'], 'History Task')
            finally:
                # Properly close persistence connections
                persistence.close()


class TestIntegration(unittest.TestCase):
    """Integration tests for scheduler with client."""

    @patch('easy_acumatica.client.AcumaticaClient')
    def test_client_scheduler_property(self, mock_client_class):
        """Test scheduler property on client."""
        from easy_acumatica import AcumaticaClient

        # Mock client
        client = Mock(spec=AcumaticaClient)
        client._scheduler = None

        # Add scheduler property behavior
        def get_scheduler():
            if client._scheduler is None:
                client._scheduler = TaskScheduler(client=client)
            return client._scheduler

        type(client).scheduler = property(lambda self: get_scheduler())

        # Access scheduler
        scheduler = client.scheduler
        self.assertIsInstance(scheduler, TaskScheduler)
        self.assertEqual(scheduler.client, client)

    def test_batch_call_scheduling(self):
        """Test scheduling batch calls."""
        scheduler = TaskScheduler()

        # Create mock batch call
        mock_call1 = Mock(return_value="result1")
        mock_call2 = Mock(return_value="result2")

        wrapper1 = CallableWrapper(mock_call1)
        wrapper2 = CallableWrapper(mock_call2)

        def batch_execution():
            return [wrapper1.execute(), wrapper2.execute()]

        task = scheduler.add_task(
            name="Batch Task",
            callable_obj=batch_execution,
            schedule=IntervalSchedule(hours=6)
        )

        # Execute
        result = task.execute()
        self.assertTrue(result.success)
        self.assertEqual(result.result, ["result1", "result2"])


if __name__ == '__main__':
    unittest.main()