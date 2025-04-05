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

        # logger.debug(f"Created Task: {self.task_id}"
        #              f"\n\tTimestamp: {self.get_time_str()}"
        #              f"\n\tMessage: {self.message[:10]}.."
        #              f"\n\tAlarm Name: {self.alarm_name}"
        #              f"\n\tVibrate: {self.vibrate}"
        #              f"\n\tExpired: {self.expired}"
        #              )
    
    def to_dict(self) -> dict:
        """Convert Task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "alarm_name": self.alarm_name,
            "vibrate": self.vibrate,
            "expired": self.expired
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary."""
        return cls(
            task_id=data.get("task_id"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().strftime("%H:%M"))),
            message=data.get("message", "Error loading task data"),
            alarm_name=data.get("alarm_name", None),
            vibrate=data.get("vibrate", False),
            expired=data.get("expired", False)
        )
    
    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return self.timestamp.strftime("%A %d %b")
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return self.timestamp.strftime("%H:%M")
