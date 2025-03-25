from datetime import datetime


class Task:
    """
    Represents a task with a message and timestamp.
    """
    def __init__(self, task_id=None, message="", timestamp=None):
        self.task_id = task_id if task_id else datetime.now().strftime("%Y%m%d%H%M%S")
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        
    def to_dict(self):
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create task from dictionary"""
        return cls(
            task_id=data.get("task_id"),
            message=data.get("message"),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )
    
    def get_date_str(self):
        """Get formatted date string [Day DD Month]"""
        if isinstance(self.timestamp, datetime):
            dt = self.timestamp
        else:
            dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%A %d %b")
    
    def get_time_str(self):
        """Get formatted time string [HH:MM]"""
        return self.timestamp.strftime("%H:%M")

    def get_task_id(self):
        """Get task id"""
        return self.task_id
