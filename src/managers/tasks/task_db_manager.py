import os
import sqlite3
import time
from datetime import datetime

from src.utils.logger import logger
from src.utils.platform import get_storage_path
from src.settings import DIR

class TaskDatabaseManager:
    """
    Manages the SQLite database for tasks.
    Provides methods to create, read, update, and delete tasks.
    """
    def __init__(self):
        # Get the database file path
        self.db_file = get_storage_path(os.path.join(DIR.ASSETS, "tasks.db"))
        self._connect_db()
        self._create_tables()
    
    def _connect_db(self):
        """
        Connect to the SQLite database.
        Create the database if it doesn't exist.
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            # Convert timestamp rows to datetime objects automatically
            self.conn.row_factory = self._dict_factory
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Use WAL mode for better concurrency and performance
            self.conn.execute("PRAGMA journal_mode = WAL")
            # Reduce fsync calls (careful with this in production)
            self.conn.execute("PRAGMA synchronous = NORMAL")
            
            logger.debug(f"Connected to database: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _dict_factory(self, cursor, row):
        """Convert row to dictionary for easier access."""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def _create_tables(self):
        """Create tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Tasks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                alarm_name TEXT,
                vibrate INTEGER DEFAULT 0,
                expired INTEGER DEFAULT 0
            )
            ''')
            
            self.conn.commit()
            logger.debug("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def get_all_tasks(self):
        """Retrieve all tasks from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY timestamp")
            tasks = cursor.fetchall()
            return tasks
        except sqlite3.Error as e:
            logger.error(f"Error retrieving tasks: {e}")
            return []
    
    def get_today_tasks(self):
        """Retrieve only today's tasks from the database."""
        try:
            today = datetime.now().date().isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE date(timestamp) = ? ORDER BY timestamp",
                (today,)
            )
            tasks = cursor.fetchall()
            return tasks
        except sqlite3.Error as e:
            logger.error(f"Error retrieving today's tasks: {e}")
            return []
    
    def get_task_by_id(self, task_id):
        """Retrieve a task by its ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            task = cursor.fetchone()
            return task
        except sqlite3.Error as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            return None
    
    def add_task(self, task_id, message, timestamp, alarm_name, vibrate, expired):
        """Add a new task to the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (task_id, message, timestamp, alarm_name, vibrate, expired) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, message, timestamp, alarm_name, 1 if vibrate else 0, 1 if expired else 0)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding task: {e}")
            return False
    
    def update_task(self, task_id, message, timestamp, alarm_name, vibrate, expired):
        """Update an existing task."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE tasks SET message = ?, timestamp = ?, alarm_name = ?, vibrate = ?, expired = ? WHERE task_id = ?",
                (message, timestamp, alarm_name, 1 if vibrate else 0, 1 if expired else 0, task_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id):
        """Delete a task from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    def mark_expired_tasks(self):
        """Mark tasks as expired if their timestamp is in the past."""
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE tasks SET expired = 1 WHERE timestamp < ? AND expired = 0",
                (now,)
            )
            self.conn.commit()
            return cursor.rowcount  # Return number of tasks marked as expired
        except sqlite3.Error as e:
            logger.error(f"Error marking expired tasks: {e}")
            return 0
            
    def save_tasks_in_bulk(self, tasks_data):
        """
        Save multiple tasks in a single transaction.
        Much faster than individual saves on Android.
        """
        try:
            cursor = self.conn.cursor()
            
            # Begin transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            for task_data in tasks_data:
                cursor.execute(
                    "INSERT OR REPLACE INTO tasks (task_id, message, timestamp, alarm_name, vibrate, expired) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        task_data["task_id"],
                        task_data["message"],
                        task_data["timestamp"],
                        task_data["alarm_name"],
                        task_data["vibrate"],
                        task_data["expired"]
                    )
                )
            
            # Commit transaction
            self.conn.commit()
            logger.debug(f"Saved {len(tasks_data)} tasks in bulk")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving tasks in bulk: {e}")
            return False
            
    def backup_database(self):
        """Create a backup of the database."""
        import shutil
        from datetime import datetime
        
        try:
            backup_dir = get_storage_path(os.path.join(DIR.ASSETS, "backups"))
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_file = os.path.join(
                backup_dir, 
                f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            # Close current connection to ensure all data is written
            self.conn.commit()
            
            # Copy the database file
            shutil.copy2(self.db_file, backup_file)
            
            logger.debug(f"Database backed up to {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False 