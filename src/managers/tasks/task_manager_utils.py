import uuid
from functools import lru_cache

from datetime import datetime


class DateFormats:
    """Date and time format patterns used throughout the application."""
    DATE_KEY = "%Y-%m-%d"              # 2024-03-21
    TIMESTAMP = "%Y-%m-%dT%H:%M:%S"    # 2024-03-21T14:30:00

    TASK_HEADER = "%A %d %b"           # Thursday 21 Mar
    TASK_TIME = "%H:%M"                # 14:30

    SELECTED_TIME = "%H:%M"            # 14:30
    CALENDAR_DAY = "%A %d"             # Thursday 21
    HOUR = "%H"                        # 14
    MINUTE = "%M"                      # 30

    MONTH_DAY = "%b %d"                # March 21
    DAY_MONTH_YEAR = "%d %b %Y"        # 21 Mar 2024

    DATE_SELECTION = "%A, %b %d, %Y"   # Thursday, March 21, 2024

    RECORDING = "%H_%M_%S"             # 14_30_45


DATE = DateFormats()


class Task:
    """
    Represents a Task with a message and timestamp.
    """
    def __init__(self, task_id=None, message="", timestamp=None, alarm_name=None,
                 vibrate=False, keep_alarming=False, expired=False):
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        self.alarm_name = alarm_name
        self.vibrate = vibrate
        self.keep_alarming = keep_alarming
        self.expired = expired

    def to_dict(self) -> dict:
        """Convert Task to dictionary for serialization."""
        timestamp = self.timestamp if type(self.timestamp) == datetime else datetime.fromisoformat(self.timestamp)
        return {
            "task_id": self.task_id,
            "timestamp": timestamp,
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "keep_alarming": self.keep_alarming,
            "expired": self.expired
        }
    
    @classmethod
    def to_class(cls, data: dict) -> "Task":
        """Convert dictionary to Task class."""
        keep_alarming = data.get("keep_alarming", False)
        return Task(
            task_id=data["task_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data["message"],
            alarm_name=data["alarm_name"],
            vibrate=data["vibrate"],
            keep_alarming=keep_alarming,
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
            "keep_alarming": self.keep_alarming,
            "expired": self.expired
        }

    @staticmethod
    @lru_cache(maxsize=32)
    def to_date_str(timestamp: datetime) -> str:
        """Get formatted date string [# Thursday 21 Mar]."""
        return timestamp.strftime(DATE.TASK_HEADER)
    
    @staticmethod
    def to_time_str(timestamp: datetime) -> str:
        """Get formatted time string [HH:MM]."""
        return timestamp.strftime(DATE.TASK_TIME)

    @lru_cache(maxsize=32)
    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return Task.to_date_str(self.timestamp)
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return Task.to_time_str(self.timestamp)
    
    def get_date_key(self) -> str:
        """
        Used by TaskManager to group Tasks by date and save to JSON as key.
        Format: YYYY-MM-DD
        """
        return self.timestamp.date().isoformat()
