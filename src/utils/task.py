import json
from datetime import datetime

class Task:
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
        """Format date as 'Day DD Month' (e.g., 'Friday 14 March')"""
        # Check if timestamp is already a datetime object
        if isinstance(self.timestamp, datetime):
            dt = self.timestamp
        else:
            dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%A %d %b")  # Format like "Friday 14 Feb"
    
    def get_time_str(self):
        """Return formatted time string for display"""
        return self.timestamp.strftime("%H:%M")  # e.g. "14:30" 