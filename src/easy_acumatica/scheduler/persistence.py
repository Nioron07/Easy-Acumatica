"""Persistence layer for scheduled tasks with JSON and SQLite support."""

import json
import sqlite3
import logging
import gc
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from .schedules import deserialize_schedule
from .task import RetryPolicy

logger = logging.getLogger(__name__)


class TaskPersistence:
    """Handles task persistence to JSON or SQLite."""

    def __init__(self, storage_type: str = "json", storage_path: Optional[Path] = None):
        """
        Initialize persistence layer.

        Args:
            storage_type: "json" or "sqlite"
            storage_path: Path to storage file
        """
        self.storage_type = storage_type
        self.storage_path = storage_path or Path.home() / '.easy_acumatica' / 'scheduler'
        self._connection = None

        if storage_type == "sqlite":
            self.storage_path = self.storage_path.with_suffix('.db')
            self._init_sqlite()
        else:
            self.storage_path = self.storage_path.with_suffix('.json')

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_sqlite(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    max_runs INTEGER,
                    retry_policy TEXT,
                    metadata TEXT,
                    priority INTEGER DEFAULT 0,
                    status TEXT,
                    last_run TEXT,
                    next_run TEXT,
                    run_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    task_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    success INTEGER,
                    result TEXT,
                    error TEXT,
                    execution_time REAL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            conn.commit()

    def save_task(self, task_data: Dict[str, Any]):
        """Save a single task."""
        if self.storage_type == "sqlite":
            self._save_task_sqlite(task_data)
        else:
            self._save_task_json(task_data)

    def _save_task_sqlite(self, task_data: Dict[str, Any]):
        """Save task to SQLite."""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tasks (
                    id, name, schedule, enabled, max_runs, retry_policy,
                    metadata, priority, status, last_run, next_run,
                    run_count, error_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_data['id'],
                task_data['name'],
                json.dumps(task_data['schedule']),
                task_data.get('enabled', True),
                task_data.get('max_runs'),
                json.dumps(task_data.get('retry_policy')) if task_data.get('retry_policy') else None,
                json.dumps(task_data.get('metadata', {})),
                task_data.get('priority', 0),
                task_data.get('status'),
                task_data.get('last_run'),
                task_data.get('next_run'),
                task_data.get('run_count', 0),
                task_data.get('error_count', 0),
                datetime.now().isoformat()
            ))
            conn.commit()

    def _save_task_json(self, task_data: Dict[str, Any]):
        """Save task to JSON."""
        tasks = self.load_all_tasks()
        tasks[task_data['id']] = task_data

        with open(self.storage_path, 'w') as f:
            json.dump(tasks, f, indent=2)

    def save_all_tasks(self, tasks: Dict[str, Dict[str, Any]]):
        """Save all tasks at once."""
        if self.storage_type == "sqlite":
            for task_data in tasks.values():
                self._save_task_sqlite(task_data)
        else:
            with open(self.storage_path, 'w') as f:
                json.dump(tasks, f, indent=2)

    def load_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Load all tasks."""
        if self.storage_type == "sqlite":
            return self._load_tasks_sqlite()
        else:
            return self._load_tasks_json()

    def _load_tasks_sqlite(self) -> Dict[str, Dict[str, Any]]:
        """Load tasks from SQLite."""
        tasks = {}
        try:
            with sqlite3.connect(self.storage_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('SELECT * FROM tasks')

                for row in cursor:
                    task_data = dict(row)
                    task_data['schedule'] = json.loads(task_data['schedule'])
                    if task_data.get('retry_policy'):
                        task_data['retry_policy'] = json.loads(task_data['retry_policy'])
                    if task_data.get('metadata'):
                        task_data['metadata'] = json.loads(task_data['metadata'])
                    tasks[task_data['id']] = task_data
        except Exception as e:
            logger.error(f"Error loading tasks from SQLite: {e}")

        return tasks

    def _load_tasks_json(self) -> Dict[str, Dict[str, Any]]:
        """Load tasks from JSON."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks from JSON: {e}")
            return {}

    def delete_task(self, task_id: str):
        """Delete a task."""
        if self.storage_type == "sqlite":
            with sqlite3.connect(self.storage_path) as conn:
                conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.execute('DELETE FROM task_history WHERE task_id = ?', (task_id,))
                conn.commit()
        else:
            tasks = self.load_all_tasks()
            tasks.pop(task_id, None)
            self.save_all_tasks(tasks)

    def save_task_result(self, task_result: Dict[str, Any]):
        """Save task execution result."""
        if self.storage_type == "sqlite":
            with sqlite3.connect(self.storage_path) as conn:
                conn.execute('''
                    INSERT INTO task_history (
                        task_id, task_name, start_time, end_time,
                        success, result, error, execution_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_result['task_id'],
                    task_result['task_name'],
                    task_result['start_time'],
                    task_result['end_time'],
                    task_result['success'],
                    task_result.get('result'),
                    task_result.get('error'),
                    task_result.get('execution_time', 0.0)
                ))
                conn.commit()

    def get_task_history(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history."""
        if self.storage_type == "sqlite":
            with sqlite3.connect(self.storage_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM task_history
                    WHERE task_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ''', (task_id, limit))

                return [dict(row) for row in cursor]
        return []

    def clear_history(self, task_id: Optional[str] = None):
        """Clear task history."""
        if self.storage_type == "sqlite":
            with sqlite3.connect(self.storage_path) as conn:
                if task_id:
                    conn.execute('DELETE FROM task_history WHERE task_id = ?', (task_id,))
                else:
                    conn.execute('DELETE FROM task_history')
                conn.commit()

    def close(self):
        """Close any open connections and cleanup resources."""
        if self.storage_type == "sqlite":
            # Force garbage collection to release any lingering connections
            gc.collect()
            # Small delay to ensure Windows releases file locks
            time.sleep(0.1)

    def __del__(self):
        """Cleanup on deletion."""
        self.close()