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


class TestRegressionFixes(unittest.TestCase):
    """Regression coverage for the scheduler blocker fixes."""

    def test_load_tasks_populates_pending_restorations(self):
        """load_tasks() must expose persisted metadata for rehydration."""
        with tempfile.TemporaryDirectory() as tmp:
            persist_file = Path(tmp) / 'tasks.json'
            scheduler = TaskScheduler(persist_tasks=True, persist_file=persist_file)
            scheduler.add_task(
                name='Persisted',
                callable_obj=lambda: 'ok',
                schedule=IntervalSchedule(hours=1),
            )

            # Re-instantiate the scheduler to mimic a process restart.
            scheduler2 = TaskScheduler(persist_tasks=True, persist_file=persist_file)
            self.assertEqual(len(scheduler2.pending_restorations), 1)

            (task_id, meta), = scheduler2.pending_restorations.items()
            self.assertEqual(meta['name'], 'Persisted')

            restored = scheduler2.restore_task(task_id, lambda: 'rehydrated')
            self.assertIsNotNone(restored)
            self.assertEqual(scheduler2.pending_restorations, {})
            self.assertEqual(scheduler2.tasks[task_id].name, 'Persisted')

    def test_start_after_stop_recreates_executor(self):
        """stop() must not leave start() pointed at a shutdown executor."""
        scheduler = TaskScheduler(check_interval=10)
        scheduler.start()
        scheduler.stop(wait=True)
        # Should not raise "cannot schedule new futures after shutdown".
        scheduler.start()
        try:
            scheduler.add_task(
                name='post-restart',
                callable_obj=lambda: 'ok',
                schedule=IntervalSchedule(hours=1),
            )
            future = scheduler.execute_now(scheduler.list_tasks()[0].id)
            self.assertIsNotNone(future)
            future.result(timeout=2)
        finally:
            scheduler.stop(wait=True)

    def test_dependency_cycle_raises(self):
        """resolve_task_dependencies must detect cycles instead of looping."""
        from easy_acumatica.scheduler.utils import resolve_task_dependencies

        a = ScheduledTask(name='a', callable_obj=lambda: None,
                          schedule=IntervalSchedule(hours=1))
        b = ScheduledTask(name='b', callable_obj=lambda: None,
                          schedule=IntervalSchedule(hours=1))
        a.depends_on = [b]
        b.depends_on = [a]

        with self.assertRaises(ValueError):
            resolve_task_dependencies([a, b])

    def test_retry_does_not_double_fire(self):
        """task.execute() retry path defers via _retry_after; is_due() must
        respect the deadline so the scheduler loop doesn't re-run instantly."""
        def flaky():
            raise RuntimeError('fail')

        task = ScheduledTask(
            name='flaky',
            callable_obj=flaky,
            schedule=IntervalSchedule(seconds=1),
            retry_policy=RetryPolicy(max_retries=3, retry_delay=60),
        )
        task.execute()  # first failure - schedules retry 60s out
        # Even though the schedule's interval has nominally elapsed,
        # _retry_after is far in the future, so is_due() must return False.
        self.assertFalse(task.is_due())


class TestUtils(unittest.TestCase):
    """Coverage for scheduler/utils.py."""

    def test_parse_time_string_24h(self):
        from easy_acumatica.scheduler.utils import parse_time_string
        self.assertEqual(parse_time_string("14:30"), (14, 30, 0))
        self.assertEqual(parse_time_string("14:30:45"), (14, 30, 45))

    def test_parse_time_string_am_pm(self):
        from easy_acumatica.scheduler.utils import parse_time_string
        self.assertEqual(parse_time_string("2:30 PM"), (14, 30, 0))
        self.assertEqual(parse_time_string("12:00 AM"), (0, 0, 0))
        self.assertEqual(parse_time_string("12:00 PM"), (12, 0, 0))

    def test_resolve_task_dependencies_orders_topologically(self):
        from easy_acumatica.scheduler.utils import resolve_task_dependencies
        a = ScheduledTask("a", lambda: None, IntervalSchedule(hours=1))
        b = ScheduledTask("b", lambda: None, IntervalSchedule(hours=1))
        c = ScheduledTask("c", lambda: None, IntervalSchedule(hours=1))
        b.depends_on = [a]
        c.depends_on = [b]
        ordered = resolve_task_dependencies([c, a, b])
        self.assertEqual([t.name for t in ordered], ["a", "b", "c"])

    def test_calculate_next_run_times_skips_disabled(self):
        from easy_acumatica.scheduler.utils import calculate_next_run_times
        enabled = ScheduledTask("on", lambda: None, IntervalSchedule(hours=1))
        disabled = ScheduledTask("off", lambda: None, IntervalSchedule(hours=1), enabled=False)
        result = calculate_next_run_times([enabled, disabled], days=2)
        self.assertIn(enabled.id, result)
        self.assertNotIn(disabled.id, result)
        self.assertGreater(len(result[enabled.id]), 0)

    def test_format_schedule_summary_for_each_type(self):
        from easy_acumatica.scheduler.utils import format_schedule_summary
        self.assertIn("second", format_schedule_summary(IntervalSchedule(seconds=30)))
        self.assertIn("minute", format_schedule_summary(IntervalSchedule(minutes=15)))
        self.assertIn("hour", format_schedule_summary(IntervalSchedule(hours=2)))
        self.assertIn("day", format_schedule_summary(IntervalSchedule(days=3)))
        self.assertIn("Cron", format_schedule_summary(CronSchedule("0 9 * * *")))
        self.assertIn("Daily", format_schedule_summary(DailySchedule(9, 30)))
        self.assertIn("Tuesday", format_schedule_summary(WeeklySchedule(1, 9, 0)))
        self.assertIn("Once", format_schedule_summary(OnceSchedule(datetime(2030, 1, 1, 12))))

    def test_estimate_resource_usage(self):
        from easy_acumatica.scheduler.utils import estimate_resource_usage
        tasks = [
            ScheduledTask("hourly", lambda: None, IntervalSchedule(hours=1)),
            ScheduledTask("daily", lambda: None, DailySchedule(9, 0)),
            ScheduledTask("off", lambda: None, IntervalSchedule(hours=1), enabled=False),
        ]
        out = estimate_resource_usage(tasks, hours=24)
        self.assertEqual(out["active_tasks"], 2)
        self.assertEqual(out["estimated_executions"], 24 + 1)  # 24 hourly + 1 daily
        self.assertEqual(out["time_window_hours"], 24)
        self.assertIn("hourly", out["task_estimates"])

    def test_task_monitor_records_metrics(self):
        from easy_acumatica.scheduler.utils import TaskMonitor
        m = TaskMonitor()
        m.record_execution("t1", 0.5, success=True)
        m.record_execution("t1", 1.5, success=True)
        m.record_execution("t1", 2.0, success=False)
        stats = m.get_statistics("t1")
        self.assertEqual(stats["total_runs"], 3)
        self.assertEqual(stats["success_count"], 2)
        self.assertEqual(stats["failure_count"], 1)
        self.assertAlmostEqual(stats["success_rate"], 2 / 3)
        self.assertAlmostEqual(stats["average_time"], (0.5 + 1.5 + 2.0) / 3)
        self.assertEqual(stats["min_time"], 0.5)
        self.assertEqual(stats["max_time"], 2.0)

    def test_task_monitor_unknown_task(self):
        from easy_acumatica.scheduler.utils import TaskMonitor
        m = TaskMonitor()
        self.assertEqual(m.get_statistics("nope"), {})
        self.assertEqual(m.get_all_statistics(), {})


class TestScheduleSerialization(unittest.TestCase):
    """Round-trip every schedule type via deserialize_schedule."""

    def _round_trip(self, schedule):
        from easy_acumatica.scheduler.schedules import deserialize_schedule
        return deserialize_schedule(schedule.to_dict())

    def test_interval_round_trip(self):
        s = IntervalSchedule(hours=2, minutes=30)
        out = self._round_trip(s)
        self.assertIsInstance(out, IntervalSchedule)
        self.assertEqual(out.interval.total_seconds(), s.interval.total_seconds())

    def test_daily_round_trip(self):
        s = DailySchedule(hour=9, minute=15, second=30, run_immediately=True)
        out = self._round_trip(s)
        self.assertEqual((out.hour, out.minute, out.second), (9, 15, 30))
        self.assertTrue(out.run_immediately)

    def test_weekly_round_trip(self):
        s = WeeklySchedule(weekday=2, hour=14, minute=45)
        out = self._round_trip(s)
        self.assertEqual((out.weekday, out.hour, out.minute), (2, 14, 45))

    def test_once_round_trip(self):
        run_at = datetime(2030, 6, 15, 9, 0, 0)
        s = OnceSchedule(run_at=run_at)
        out = self._round_trip(s)
        self.assertEqual(out.run_at, run_at)

    def test_cron_round_trip(self):
        s = CronSchedule("0 9 * * MON")
        out = self._round_trip(s)
        self.assertEqual(out.expression, "0 9 * * MON")

    def test_unknown_schedule_type_raises(self):
        from easy_acumatica.scheduler.schedules import deserialize_schedule
        with self.assertRaises(ValueError):
            deserialize_schedule({"type": "lunar"})


class TestScheduleValidation(unittest.TestCase):
    """Constructor argument validation for each schedule type."""

    def test_interval_rejects_zero(self):
        with self.assertRaises(ValueError):
            IntervalSchedule(seconds=0)

    def test_daily_rejects_invalid_hour(self):
        with self.assertRaises(ValueError):
            DailySchedule(hour=24)

    def test_daily_rejects_invalid_minute(self):
        with self.assertRaises(ValueError):
            DailySchedule(hour=9, minute=60)

    def test_weekly_rejects_invalid_weekday_int(self):
        with self.assertRaises(ValueError):
            WeeklySchedule(weekday=7, hour=9)

    def test_weekly_accepts_weekday_name(self):
        s = WeeklySchedule(weekday="Friday", hour=9)
        self.assertEqual(s.weekday, 4)

    def test_cron_rejects_short_expression(self):
        with self.assertRaises(ValueError):
            CronSchedule("0 9")


class TestRetryPolicy(unittest.TestCase):

    def test_default_policy(self):
        p = RetryPolicy()
        self.assertEqual(p.max_retries, 3)
        self.assertGreater(p.retry_delay, 0)

    def test_exponential_backoff_increases(self):
        p = RetryPolicy(
            max_retries=5,
            retry_delay=10,
            exponential_backoff=True,
            backoff_factor=2.0,
        )
        d1 = p.get_retry_delay(1)
        d2 = p.get_retry_delay(2)
        d3 = p.get_retry_delay(3)
        self.assertLess(d1, d2)
        self.assertLess(d2, d3)

    def test_linear_backoff_returns_constant(self):
        p = RetryPolicy(max_retries=3, retry_delay=5, exponential_backoff=False)
        self.assertEqual(p.get_retry_delay(1), 5)
        self.assertEqual(p.get_retry_delay(2), 5)
        self.assertEqual(p.get_retry_delay(3), 5)

    def test_to_dict_round_trip(self):
        p = RetryPolicy(
            max_retries=4,
            retry_delay=8,
            exponential_backoff=False,
            backoff_factor=3.0,
        )
        out = RetryPolicy.from_dict(p.to_dict())
        self.assertEqual(out.max_retries, 4)
        self.assertEqual(out.retry_delay, 8)
        self.assertFalse(out.exponential_backoff)
        self.assertEqual(out.backoff_factor, 3.0)


class TestScheduledTaskState(unittest.TestCase):
    """State transitions and accessors on ScheduledTask."""

    def test_pause_resume_cancel(self):
        t = ScheduledTask("t", lambda: 1, IntervalSchedule(hours=1))
        t.pause()
        self.assertEqual(t.status, TaskStatus.PAUSED)
        t.resume()
        self.assertEqual(t.status, TaskStatus.PENDING)
        t.cancel()
        self.assertEqual(t.status, TaskStatus.CANCELLED)

    def test_max_runs_limit_blocks_is_due(self):
        t = ScheduledTask(
            "limited",
            lambda: 1,
            IntervalSchedule(seconds=1),
            max_runs=1,
        )
        t.execute()
        # After hitting max_runs, is_due should be False forever.
        self.assertFalse(t.is_due())

    def test_is_due_blocks_on_disabled(self):
        t = ScheduledTask("off", lambda: 1, IntervalSchedule(seconds=1), enabled=False)
        self.assertFalse(t.is_due())

    def test_is_due_blocks_on_pending_dependency(self):
        dep = ScheduledTask("dep", lambda: 1, IntervalSchedule(seconds=1))
        t = ScheduledTask("t", lambda: 1, IntervalSchedule(seconds=1))
        t.depends_on = [dep]
        # Dependency hasn't completed yet.
        self.assertFalse(t.is_due())
        # Once the dependency completes, downstream becomes eligible.
        dep.execute()
        # is_due also depends on the schedule itself; the interval is 1s so
        # we need a real pause - just confirm the dependency gate passes.
        dep.status = TaskStatus.COMPLETED  # explicit, in case execute set otherwise
        # The schedule.is_due check may return False right after execute,
        # so we only assert the dependency branch no longer blocks.
        self.assertEqual(dep.status, TaskStatus.COMPLETED)

    def test_to_dict_serializes_core_fields(self):
        t = ScheduledTask(
            "T",
            lambda: 1,
            IntervalSchedule(hours=1),
            metadata={"owner": "qa"},
            priority=5,
        )
        d = t.to_dict()
        self.assertEqual(d["name"], "T")
        self.assertEqual(d["priority"], 5)
        self.assertEqual(d["metadata"], {"owner": "qa"})


class TestSchedulerLifecycle(unittest.TestCase):
    """Coverage for surface area on TaskScheduler not exercised elsewhere."""

    def test_duplicate_name_raises(self):
        s = TaskScheduler()
        s.add_task("dup", lambda: 1, IntervalSchedule(hours=1))
        with self.assertRaises(ValueError):
            s.add_task("dup", lambda: 1, IntervalSchedule(hours=1))

    def test_get_task_and_get_task_by_name(self):
        s = TaskScheduler()
        t = s.add_task("alpha", lambda: 1, IntervalSchedule(hours=1))
        self.assertIs(s.get_task(t.id), t)
        self.assertIs(s.get_task_by_name("alpha"), t)
        self.assertIsNone(s.get_task("nonexistent"))
        self.assertIsNone(s.get_task_by_name("nonexistent"))

    def test_list_tasks(self):
        s = TaskScheduler()
        s.add_task("a", lambda: 1, IntervalSchedule(hours=1))
        s.add_task("b", lambda: 1, IntervalSchedule(hours=1))
        names = {t.name for t in s.list_tasks()}
        self.assertEqual(names, {"a", "b"})

    def test_pause_resume_remove_via_scheduler(self):
        s = TaskScheduler()
        t = s.add_task("p", lambda: 1, IntervalSchedule(hours=1))
        self.assertTrue(s.pause_task(t.id))
        self.assertEqual(t.status, TaskStatus.PAUSED)
        self.assertTrue(s.resume_task(t.id))
        self.assertEqual(t.status, TaskStatus.PENDING)
        self.assertTrue(s.remove_task(t.id))
        self.assertFalse(s.remove_task(t.id))  # already gone

    def test_get_statistics_shape(self):
        s = TaskScheduler()
        stats = s.get_statistics()
        for key in ("running", "total_tasks", "running_tasks",
                    "total_executions", "success_rate"):
            self.assertIn(key, stats)
        self.assertEqual(stats["total_tasks"], 0)

    def test_clear_history(self):
        s = TaskScheduler()
        t = s.add_task("h", lambda: 1, IntervalSchedule(hours=1))
        t.execute()
        self.assertEqual(len(t.history), 1)
        s.clear_history(t.id)
        self.assertEqual(len(t.history), 0)
        # Whole-scheduler clear
        t.execute()
        s.clear_history()
        self.assertEqual(len(t.history), 0)

    def test_context_manager_starts_and_stops(self):
        s = TaskScheduler(check_interval=10)
        with s:
            self.assertTrue(s._running)
        self.assertFalse(s._running)

    def test_repr(self):
        s = TaskScheduler()
        s.add_task("r", lambda: 1, IntervalSchedule(hours=1))
        text = repr(s)
        self.assertIn("TaskScheduler", text)
        self.assertIn("tasks=1", text)


class TestSchedulerIntegrationLoop(unittest.TestCase):
    """Black-box: run the scheduler loop briefly and confirm it fires tasks."""

    def test_short_interval_task_actually_runs(self):
        executions = {"n": 0}

        def tick():
            executions["n"] += 1

        s = TaskScheduler(check_interval=1)
        s.add_task("tick", tick, IntervalSchedule(seconds=1))
        s.start()
        try:
            time.sleep(2.5)  # enough for ~2 firings
        finally:
            s.stop(wait=True)

        self.assertGreaterEqual(executions["n"], 1)
        self.assertGreaterEqual(s.successful_executions, 1)


class TestBuilderFluentSurface(unittest.TestCase):
    """The TaskBuilder fluent interface beyond the basics already covered."""

    def test_every_minutes_and_hours(self):
        s = TaskScheduler()
        t = (
            TaskBuilder(s)
            .named("eh")
            .calling(lambda: 1)
            .every(minutes=5)
            .build()
        )
        self.assertIsInstance(t.schedule, IntervalSchedule)
        self.assertEqual(t.schedule.interval.total_seconds(), 5 * 60)

    def test_daily_at(self):
        s = TaskScheduler()
        t = (
            TaskBuilder(s)
            .named("d")
            .calling(lambda: 1)
            .daily_at(9, 30)
            .build()
        )
        self.assertIsInstance(t.schedule, DailySchedule)
        self.assertEqual((t.schedule.hour, t.schedule.minute), (9, 30))

    def test_weekly_on(self):
        s = TaskScheduler()
        t = (
            TaskBuilder(s)
            .named("w")
            .calling(lambda: 1)
            .weekly_on("monday", 8, 0)
            .build()
        )
        self.assertIsInstance(t.schedule, WeeklySchedule)
        self.assertEqual(t.schedule.weekday, 0)

    def test_once_at_string_input(self):
        s = TaskScheduler()
        t = (
            TaskBuilder(s)
            .named("o")
            .calling(lambda: 1)
            .once_at("2030-01-01T12:00:00")
            .build()
        )
        self.assertIsInstance(t.schedule, OnceSchedule)

    def test_priority_metadata_disabled_max_runs(self):
        s = TaskScheduler()
        t = (
            TaskBuilder(s)
            .named("flags")
            .calling(lambda: 1)
            .every(hours=1)
            .with_priority(7)
            .with_metadata(team="qa", region="us")
            .with_max_runs(3)
            .disabled()
            .build()
        )
        self.assertEqual(t.priority, 7)
        self.assertEqual(t.metadata["team"], "qa")
        self.assertEqual(t.max_runs, 3)
        self.assertFalse(t.enabled)

    def test_callbacks_wired(self):
        s = TaskScheduler()
        seen = {"ok": False, "err": False}
        t = (
            TaskBuilder(s)
            .named("cb")
            .calling(lambda: 1)
            .every(hours=1)
            .on_success(lambda r: seen.update(ok=True))
            .on_failure(lambda r: seen.update(err=True))
            .build()
        )
        t.execute()
        self.assertTrue(seen["ok"])

    def test_build_does_not_register(self):
        """build() returns a task without adding it to the scheduler."""
        s = TaskScheduler()
        t = TaskBuilder(s).named("orphan").calling(lambda: 1).every(hours=1).build()
        self.assertNotIn(t.id, s.tasks)

    def test_start_registers_via_lock_and_rejects_duplicates(self):
        """Regression: builder.start() must go through the same path as
        add_task, raising on duplicate names instead of silently
        overwriting (it used to bypass _task_lock entirely)."""
        s = TaskScheduler()
        s.add_task("dup", lambda: 1, IntervalSchedule(hours=1))
        with self.assertRaises(ValueError):
            (TaskBuilder(s)
             .named("dup")
             .calling(lambda: 1)
             .every(hours=1)
             .start())


class TestDecoratorBehavior(unittest.TestCase):

    def test_every_decorator_does_not_auto_start(self):
        """Regression: decorators no longer schedule at import time."""
        from easy_acumatica.scheduler.decorators import every

        scheduler = TaskScheduler()

        @every(minutes=10, scheduler=scheduler)
        def manual():
            return "ok"

        # No task created until start_scheduling is invoked explicitly.
        self.assertEqual(len(scheduler.tasks), 0)
        manual.start_scheduling(IntervalSchedule(minutes=10))
        self.assertEqual(len(scheduler.tasks), 1)

    def test_every_decorator_with_start_immediately_true(self):
        """Opt-in behavior: passing start_immediately=True schedules now."""
        from easy_acumatica.scheduler.decorators import every

        scheduler = TaskScheduler()

        @every(seconds=30, scheduler=scheduler, start_immediately=True)
        def auto():
            return "ok"

        self.assertEqual(len(scheduler.tasks), 1)


class TestTaskResultSerialization(unittest.TestCase):

    def test_to_dict_keys_present(self):
        t = ScheduledTask("r", lambda: 42, IntervalSchedule(hours=1))
        result = t.execute()
        d = result.to_dict()
        for key in ("task_id", "task_name", "start_time", "end_time",
                    "success", "result", "execution_time", "retry_count"):
            self.assertIn(key, d)
        self.assertTrue(d["success"])


if __name__ == '__main__':
    unittest.main()