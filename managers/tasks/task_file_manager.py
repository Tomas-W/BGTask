import json
import time

from datetime import datetime, timedelta

from typing import Any, TYPE_CHECKING


from managers.device.device_manager import DM
from src.utils.logger import logger

if TYPE_CHECKING:
    from managers.tasks.task import Task


class TaskFileManager:

    TASK_HISTORY_DAYS: int = 30

    """
    Manages the Task file.
    """
    def __init__(self):
        self.task_file_path: str = DM.PATH.TASK_FILE
        if not self._validate_task_data():
            self._reset_task_file()

    def get_task_data(self) -> dict[str, list[dict[str, Any]]]:
        """Returns a dictionary of Tasks from the Task file."""
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            logger.error(f"Error getting Task data: {e}")
            return {}
    
    def save_task_file(self, data: dict) -> None:
        """Saves Task data to file."""
        try:
            with open(self.task_file_path, "w") as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving Task file: {e}")
    
    def _save_task_changes(self, task_id: str, changes: dict) -> None:
        """Saves Task changes to file."""
        try:
            task_data = self.get_task_data()
            for date_tasks in task_data.values():
                for task in date_tasks:
                    if task["task_id"] == task_id:
                        task.update(changes)
                        self.save_task_file(task_data)
                        
                        time.sleep(0.1)
                        logger.debug(f"Saved changes for Task {DM.get_task_id_log(task_id)}")
                        return
        
        except Exception as e:
            logger.error(f"Error saving Task changes: {e}")
    
    def _validate_task_data(self) -> bool:
        """
        Returns True if TaskData is valid, False otherwise.
        """
        data = self.get_task_data()

        if not isinstance(data, dict):
            return False
        
        for date_key, tasks_data in data.items():
            # Check date_key isstring
            if not isinstance(date_key, str):
                logger.error(f"Error validating TaskData, date_key != str: {type(date_key)=}")
                return False
            
            # Check tasks_data is list
            if not isinstance(tasks_data, list):
                logger.error(f"Error validating TaskData, tasks_data != list: {type(tasks_data)=}")
                return False
            
            # Check Tasks are dicts
            for task_data in tasks_data:
                if not isinstance(task_data, dict):
                    logger.error(f"Error validating TaskData, task_data != dict: {type(task_data)=}")
                    return False
        
        return True
    
    def _reset_task_file(self) -> None:
        """Saves empty JSON to file."""
        try:
            data = {}
            self.save_task_file(data)
        
        except Exception as e:
            logger.error(f"Error resetting Task file: {e}")
    
    def _add_to_task_groups(self, task: "Task") -> None:
        """
        Adds a Task to the task_groups in the JSON file.
        """
        try:
            task_data = self.get_task_data()
            date_key = task.get_date_key()
            task.expired = False
            task_json = task.to_json()
            # Add to existing DateGroup or create new one
            if date_key in task_data:
                task_data[date_key].append(task_json)
            else:
                task_data[date_key] = [task_json]
            
            self.save_task_file(task_data)
            
            time.sleep(0.1)
            logger.debug(f"Added Task to group {date_key}: {DM.get_task_log(task)}")
            
        except Exception as e:
            logger.error(f"Error adding Task to groups: {e}")
    
    def _remove_from_task_groups(self, task: "Task", date_key: str = None) -> None:
        """
        Removes a Task from the task_groups in the JSON file.
        If the last task is removed from a group, the entire group is removed.
        If no date_key is priveded, the Task's date_key is used.
        """
        try:
            task_data = self.get_task_data()
            date_key = date_key if date_key else task.get_date_key()
            
            if date_key not in task_data:
                logger.error(f"Date key {date_key} not found in task data")
                return
            
            # Find and remove the task
            tasks_in_date = task_data[date_key]
            for i, task_dict in enumerate(tasks_in_date):
                if task_dict["task_id"] == task.task_id:
                    tasks_in_date.pop(i)
                    
                    # If last Task in group, remove it
                    if not tasks_in_date:
                        del task_data[date_key]
                    
                    self.save_task_file(task_data)
                    
                    time.sleep(0.1)
                    logger.debug(f"Removed Task from group {date_key}: {DM.get_task_log(task)}")
                    return
            
            logger.error(f"Task {DM.get_task_log(task)} not found in group {date_key}")
            
        except Exception as e:
            logger.error(f"Error removing Task from groups: {e}")
    
    def _remove_old_task_groups(self) -> None:
        """
        Removes TaskGroups that are older than TASK_HISTORY_DAYS.
        """
        try:
            data = self.get_task_data()
            if not data:
                return
            
            # Get earliest date to keep
            earliest_date = datetime.now().date() - timedelta(days=TaskFileManager.TASK_HISTORY_DAYS)
            earliest_date_str = earliest_date.isoformat()

            # Remove old TaskGroups
            old_groups_removed = False
            keys_to_remove = []
            for date_key in data.keys():
                if date_key < earliest_date_str:
                    keys_to_remove.append(date_key)
                    old_groups_removed = True
            
            # Remove old keys
            for key in keys_to_remove:
                del data[key]
            
            # Save if needed
            if old_groups_removed:
                self.save_task_file(data)
                logger.debug(f"Removed {len(keys_to_remove)} old TaskGroups")
        
        except Exception as e:
            logger.error(f"Error removing old TaskGroups: {e}")
