import json
import time

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.event import EventDispatcher

from managers.device.device_manager import DM
from managers.tasks.task import Task, TaskGroup

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_expiry_manager import AppExpiryManager
    from src.app_managers.app_communication_manager import AppCommunicationManager

class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage using JSON.
    """

    DAYS_IN_PAST: int = 1
    TASK_HISTORY_DAYS: int = 30
    FIRST_TASK_MESSAGE = "No upcomming Tasks!\n\nPress + to add a new one,\nor select a Task to edit or delete."

    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.expiry_manager: "AppExpiryManager" = app.expiry_manager
        self.communication_manager: "AppCommunicationManager" = None  # connected in main.py

        # Task file
        self.task_file_path: str = DM.PATH.TASK_FILE
        if not DM.validate_file(self.task_file_path):
            return

        # Task groups
        self.task_groups: list[TaskGroup] = self.get_task_groups()
        self.current_task_group: TaskGroup | None = self.get_current_task_group()

        # New/Edit Task attributes
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None
        self.selected_vibrate: bool = False
        # Editing Task attributes
        self.task_to_edit: Task | None = None
        
        Clock.schedule_interval(self.expiry_manager.check_task_expiry, 1)
    
    def get_task_groups(self) -> list[TaskGroup]:
        """
        Loads all Tasks from the last TASK_HISTORY_DAYS days, which are grouped by date.
        Returns a list of sorted TaskGroup objects with sorted Tasks, earliest first.
        """
        start_time = time.time()
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            
            # Get earliest date to include
            earliest_date = datetime.now().date() - timedelta(days=TaskManager.TASK_HISTORY_DAYS)
            task_groups = []
            for date_key, tasks_data in data.items():
                task_date = datetime.strptime(date_key, DM.DATE.DATE_KEY).date()
                # Only include dates in range
                if task_date >= earliest_date:
                    # Sort by effective time
                    tasks = [Task.to_class(task_data) for task_data in tasks_data]
                    sorted_tasks = sorted(tasks, key=lambda x: x.timestamp + timedelta(seconds=x.snooze_time))
                    task_groups.append(TaskGroup(date_str=date_key, tasks=sorted_tasks))
            
            # Sort by date
            sorted_task_groups = sorted(task_groups, key=lambda x: x.date_str)
            logger.error(f"Loading Task groups took: {round(time.time() - start_time, 6)} seconds")
            return sorted_task_groups
        
        except Exception as e:
            logger.error(f"Error loading Task groups: {e}")
            return []
    
    def get_current_task_group(self, task: Task | None = None) -> TaskGroup | None:
        """
        Gets the current TaskGroup, the TaskGroup of the given Task or the welcome TaskGroup.
        """
        if not self.task_groups:
            self._set_welcome_task_group()
            return self.get_current_task_group()

        if task is None:
            date_key = datetime.now().date().isoformat()
        else:
            date_key = task.get_date_key()
        
        for task_group in self.task_groups:
            if task_group.date_str >= date_key and task_group.tasks:
                return task_group
        
        logger.critical(f"No TaskGroup found for date: {date_key}")
        return None

    def _set_welcome_task_group(self) -> None:
        """Sets the welcome TaskGroup in the TaskManager."""
        first_task = Task(
            message=TaskManager.FIRST_TASK_MESSAGE,
            timestamp=datetime.now() - timedelta(minutes=1),
            expired=True,
        )
        start_group = TaskGroup(date_str=first_task.get_date_key(),
                                tasks=[first_task])
        self.task_groups = [start_group]
        self.save_task_groups()
    
    def refresh_task_groups(self) -> None:
        """
        Refreshes the Task groups.
        """
        self.task_groups = self.get_task_groups()
    
    def save_task_groups(self) -> None:
        """
        Saves the Task groups to the file.
        """
        try:
            # Convert TaskGroups to the expected dictionary format
            tasks_json = {}
            for task_group in self.task_groups:
                tasks_json[task_group.date_str] = [task.to_json() for task in task_group.tasks]
            
            with open(self.task_file_path, "w") as f:
                json.dump(tasks_json, f, indent=2)
            time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error saving Task groups: {e}")
    
    def _add_to_task_groups(self, task: Task) -> None:
        """
        Adds a Task to the TaskGroups.
        """
        date_key = task.get_date_key()
        for task_group in self.task_groups:
            if task_group.date_str == date_key:
                task_group.tasks.append(task)
                break
        else:
            self.task_groups.append(TaskGroup(date_str=date_key, tasks=[task]))
    
    def _remove_from_task_groups(self, task: Task) -> None:
        """
        Removes a Task from the TaskGroups.
        If the last task is removed from a group, the entire group is removed.
        """
        date_key = task.get_date_key()
        for i, task_group in enumerate(self.task_groups):
            if task_group.date_str == date_key:
                # Find the task by ID instead of object reference
                for j, group_task in enumerate(task_group.tasks):
                    if group_task.task_id == task.task_id:
                        task_group.tasks.pop(j)
                        
                        # If this was the last task in the group, remove the entire group
                        if not task_group.tasks:
                            self.task_groups.pop(i)
                        
                        return
                break
        else:
            logger.error(f"Error removing Task from TaskGroups, {DM.get_task_log(task)} not found")
    
    def get_task_by_id_(self, task_id: str) -> Task | None:
        """
        Gets a Task by its ID.
        """
        for task_group in self.task_groups:
            for task in task_group.tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def _connect_communication_manager(self, communication_manager: "AppCommunicationManager") -> None:
        """Connects the CommunicationManager to the TaskManager."""
        self.communication_manager = communication_manager
    
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Adds Task to task_groups, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate, keep_alarming=keep_alarming,
                    snooze_time=0)
        
        # Round timestamp
        task.timestamp = task.timestamp.replace(second=0, microsecond=0)
        
        # Add to TaskGroups
        self._add_to_task_groups(task)
        self.save_task_groups()
        
        # Refresh AppExpiryManager
        self.expiry_manager._refresh_tasks()
        # Refresh TaskManager
        self.refresh_task_groups()
        # Update HomeScreen
        self.update_home_after_changes(task.get_date_key())
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)

    def _edit_task_in_groups(self, task: Task, message: str, timestamp: datetime,
                            alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Directly edits a Task's attributes in the TaskGroups.
        Only moves the task between groups if the date has changed.
        """
        old_date_key = task.get_date_key()
        
        # Update task attributes
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        task.vibrate = vibrate
        task.keep_alarming = keep_alarming
        task.snooze_time = 0

        # Update expired state using rounded timestamps
        group_now = datetime.now().replace(second=0, microsecond=0)
        group_now += timedelta(seconds=1)
        if timestamp > group_now and task.expired:
            # Task from past to future, -> not expired
            task.expired = False
        elif timestamp <= group_now and not task.expired:
            # Task from future to past, -> expired
            task.expired = True
        
        new_date_key = task.get_date_key()
        
        # Only move task between groups if date has changed
        if old_date_key != new_date_key:
            self._remove_from_task_groups(task)
            self._add_to_task_groups(task)

    def update_task(self, task_id: str, message: str, timestamp: datetime,
                    alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Updates existing Task by its ID.
        Updates task_groups, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = self.get_task_by_id_(task_id)
        if not task:
            logger.error(f"Error updating Task, {DM.get_task_id_log(task_id)} not found")
            return
        
        self._edit_task_in_groups(task, message, timestamp, alarm_name, vibrate, keep_alarming)
        self.save_task_groups()
        
        # Refresh ExpiryManager
        self.expiry_manager._refresh_tasks()
        # Refresh TaskManager
        self.refresh_task_groups()
        # Update HomeScreen
        self.update_home_after_changes(task.get_date_key())
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)

    def delete_task(self, task_id: str) -> None:
        """
        Deletes a Task by ID.
        Updates task_groups, saves the Task to file,
         dispatches an event to update the Task display.
        """
        task = self.get_task_by_id_(task_id)
        date_key = task.get_date_key()
        if not task:
            logger.error(f"Error deleting Task, {DM.get_task_id_log(task_id)} not found")
            return
        
        # Remove from TaskGroups
        self._remove_from_task_groups(task)
        self.save_task_groups()
        
        # Refresh ExpiryManager
        self.expiry_manager._refresh_tasks()
        # Refresh TaskManager (this sorts the tasks)
        self.refresh_task_groups()
        # Update HomeScreen
        self.update_home_after_changes(date_key)
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
    
    def update_home_after_changes(self, date_key: str) -> None:
        """
        Updates the current TaskGroup and refreshes the HomeScreen to display the correct TaskGroup.
        """
        found = False
        for group in self.task_groups:
            if group.date_str == date_key:
                self.current_task_group = group
                found = True
                break
        
        if not found:
            self.current_task_group = self.get_current_task_group()
        
        self.app.get_screen(DM.SCREEN.HOME).refresh_home_screen()

    def get_task_by_timestamp(self, target_datetime: datetime) -> Task | None:
        """
        Get a Task object by its timestamp.
        Takes into account snooze time when checking for matches.
        Compares hours and minutes, ignoring seconds and microseconds.
        """
        target_date_key = target_datetime.strftime(DM.DATE.DATE_KEY)
        target_time = target_datetime.time()
        
        # Find TaskGroup for this date
        for task_group in self.task_groups:
            if task_group.date_str == target_date_key:
                # Check for match
                for task in task_group.tasks:
                    effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
                    if effective_time.time().hour == target_time.hour and effective_time.time().minute == target_time.minute:
                        return task
                break
        
        return None
    
    def date_is_taken(self, target_datetime: datetime) -> bool:
        """
        Check if a date and time is taken by any Task.
        Compares hours and minutes, ignoring seconds and microseconds.
        Takes into account snooze time when checking for conflicts.
        """
        target_date_key = target_datetime.strftime(DM.DATE.DATE_KEY)
        target_time = target_datetime.time()
        
        # Find the task group for this date
        for task_group in self.task_groups:
            if task_group.date_str == target_date_key:
                # Check if any task's effective time conflicts with target time
                for task in task_group.tasks:
                    if task == self.task_to_edit:
                        continue
                    effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
                    if effective_time.time().hour == target_time.hour and effective_time.time().minute == target_time.minute:
                        return True
                break
        
        return False
