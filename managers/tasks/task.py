import uuid

from datetime import datetime, timedelta
from functools import lru_cache

from managers.device.device_manager import DM


class Task:
    """Represents a Task"""
    def __init__(self, task_id=None, message="", timestamp=None, alarm_name=None,
                 vibrate=False, keep_alarming=False, expired=False, snooze_time=False):
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        self.alarm_name = alarm_name
        self.vibrate = vibrate
        self.keep_alarming = keep_alarming
        self.expired = expired
        self.snooze_time = snooze_time

    def to_dict(self) -> dict:
        """Convert Task to dictionary."""
        timestamp = self.timestamp if type(self.timestamp) == datetime else datetime.fromisoformat(self.timestamp)
        return {
            "task_id": self.task_id,
            "timestamp": timestamp,
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "keep_alarming": self.keep_alarming,
            "expired": self.expired,
            "snooze_time": self.snooze_time
        }
    
    @classmethod
    def to_class(cls, data: dict) -> "Task":
        """Convert dictionary to Task object."""
        keep_alarming = data.get("keep_alarming", False)
        return Task(
            task_id=data["task_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data["message"],
            alarm_name=data["alarm_name"],
            vibrate=data["vibrate"],
            keep_alarming=keep_alarming,
            expired=data["expired"],
            snooze_time=data["snooze_time"]
        )

    def to_json(self) -> dict:
        """Convert Task object to JSON dictionary."""
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "keep_alarming": self.keep_alarming,
            "expired": self.expired,
            "snooze_time": self.snooze_time
        }

    @staticmethod
    def to_date_str(timestamp: datetime) -> str:
        """Get formatted date string [# Thursday 21 Mar]."""
        return timestamp.strftime(DM.DATE.TASK_HEADER)
    
    @staticmethod
    def to_time_str(timestamp: datetime) -> str:
        """Get formatted time string [HH:MM]."""
        return timestamp.strftime(DM.DATE.TASK_TIME)

    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return Task.to_date_str(self.timestamp + timedelta(seconds=self.snooze_time))
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return Task.to_time_str(self.timestamp + timedelta(seconds=self.snooze_time))

    def get_snooze_str(self) -> str:
        """Get formatted snooze time string [e.g. 1h30m30s, 45m20s, 30s]."""
        if not self.snooze_time:
            return ""
        
        # Convert seconds to hours, minutes, and seconds
        days = self.snooze_time // 86400
        hours = (self.snooze_time % 86400) // 3600
        minutes = (self.snooze_time % 3600) // 60
        seconds = self.snooze_time % 60
        
        # Build the string, only including non-zero parts
        # Only uses d/h or h/m or m/s
        parts = []
        if days > 0:
            parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")

        elif hours > 0:
            parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
        
        elif minutes > 0:
            parts.append(f"{minutes}m")
            if seconds > 0:
                parts.append(f"{seconds}s")
        
        return "".join(parts)
    
    def get_date_key(self) -> str:
        """
        Used by TaskManager to group Tasks by date and save to JSON as key.
        Format: YYYY-MM-DD
        """
        return (self.timestamp + timedelta(seconds=self.snooze_time)).date().isoformat()


class TaskGroup:
    def __init__(self, date_str: str, tasks: list[Task]):
        self.date_str = date_str
        self.tasks = tasks
    
    @staticmethod
    def get_task_group_header_text(date_str: str) -> str:
        """
        Returns formatted header text for a task group.
        Uses the date_str to generate a user-friendly header.
        """
        today = datetime.now().date()
        # Convert date_str to date object
        try:
            task_date = datetime.strptime(date_str, DM.DATE.DATE_KEY).date()
        except ValueError:
            # Cannot parse date_str, return original
            return date_str
        
        # Format [Today, March 21]
        month_day = task_date.strftime(DM.DATE.MONTH_DAY)
        if task_date == today:
            return f"Today, {month_day}"
        
        elif task_date == today - timedelta(days=1):
            return f"Yesterday, {month_day}"
        
        elif task_date == today + timedelta(days=1):
            return f"Tomorrow, {month_day}"
        
        return task_date.strftime(DM.DATE.TASK_HEADER)
    
    def to_dict(self) -> dict:
        """Convert TaskGroup to dictionary."""
        return {
            "date_str": self.date_str,
            "tasks": [task.to_dict() for task in self.tasks]
        }

    def to_json(self) -> dict:
        """Convert TaskGroup to JSON dictionary."""
        return {
            "date_str": self.date_str,
            "tasks": [task.to_json() for task in self.tasks]
        }
    
