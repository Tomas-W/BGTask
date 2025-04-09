import json
import uuid

from datetime import datetime

from src.utils.logger import logger


class Task:
    """
    Represents a Task with a message and timestamp.
    """
    def __init__(self, task_id=None, message="", timestamp=None,
                 alarm_name=None, vibrate=False, expired=False):
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        self.alarm_name = alarm_name
        self.vibrate = vibrate
        self.expired = expired
    
    def to_dict(self) -> dict:
        """Convert Task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp if type(self.timestamp) == datetime else datetime.fromisoformat(self.timestamp),
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "expired": self.expired
        }
    
    @classmethod
    def to_class(cls, data: dict) -> "Task":
        """Convert dictionary to Task class."""
        return Task(
            task_id=data["task_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data["message"],
            alarm_name=data["alarm_name"],
            vibrate=data["vibrate"],
            expired=data["expired"]
        )

    def to_json(self) -> dict:
        """Convert Task to JSON dict."""
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "expired": self.expired
        }

    @staticmethod
    def to_date_str(timestamp: datetime) -> str:
        """Get formatted date string [Day DD Month]."""
        return timestamp.strftime("%A %d %b")
    
    @staticmethod
    def to_time_str(timestamp: datetime) -> str:
        """Get formatted time string [HH:MM]."""
        return timestamp.strftime("%H:%M")

    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return self.timestamp.strftime("%A %d %b")
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return self.timestamp.strftime("%H:%M")
    
    def get_date_key(self) -> str:
        """
        Get a standardized date string to use as a key for date grouping.
        Format: YYYY-MM-DD
        """
        return self.timestamp.date().isoformat()
    
    @staticmethod
    def date_from_key(date_key: str) -> datetime:
        """
        Convert a date key back to a datetime object.
        """
        return datetime.fromisoformat(date_key)
