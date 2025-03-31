import uuid

from datetime import datetime

from src.utils.logger import logger


class Task:
    """
    Represents a Task with a message and timestamp.
    """
    def __init__(self, task_id=None, message="", timestamp=None):
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        logger.debug(f"Created Task: {self.task_id} - {self.message} - {self.timestamp}")
    
    def to_dict(self) -> dict:
        """Convert Task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary."""
        return cls(
            task_id=data.get("task_id"),
            message=data.get("message", "Error loading task data"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().strftime("%H:%M")))
        )
    
    def get_date_str(self) -> str:
        """Get formatted date string [Day DD Month]."""
        return self.timestamp.strftime("%A %d %b")
    
    def get_time_str(self) -> str:
        """Get formatted time string [HH:MM]."""
        return self.timestamp.strftime("%H:%M")

    def get_task_id(self) -> str:
        return self.task_id
