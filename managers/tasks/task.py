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
    @lru_cache(maxsize=32)
    def to_date_str(timestamp: datetime) -> str:
        """Get formatted date string [# Thursday 21 Mar]."""
        return timestamp.strftime(DM.DATE.TASK_HEADER)
    
    @staticmethod
    def to_time_str(timestamp: datetime) -> str:
        """Get formatted time string [HH:MM]."""
        return timestamp.strftime(DM.DATE.TASK_TIME)

    @lru_cache(maxsize=32)
    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return Task.to_date_str(self.timestamp + timedelta(seconds=self.snooze_time))
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return Task.to_time_str(self.timestamp + timedelta(seconds=self.snooze_time))
    
    def get_date_key(self) -> str:
        """
        Used by TaskManager to group Tasks by date and save to JSON as key.
        Format: YYYY-MM-DD
        """
        return (self.timestamp + timedelta(seconds=self.snooze_time)).date().isoformat()
