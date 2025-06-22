from datetime import datetime, timedelta
from typing import Any

from managers.device.device_manager import DM

from src.utils.logger import logger


def get_service_timestamp(task: Any) -> str:
    """
    Returns the timestamp in the format of the ServiceNotification
    This includes the snooze time
    """
    try:
        timestamp = task.timestamp
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        if timestamp.date() == today:
            return f"Today @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
        
        elif timestamp.date() == tomorrow:
            return f"Tomorrow @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
        
        else:
            return f"{timestamp.strftime(DM.DATE.MONTH_DAY)} @ {timestamp.strftime(DM.DATE.TASK_TIME)}"
    
    except Exception as e:
        logger.error(f"Error getting service timestamp: {e}")
        return "00:00:00"
