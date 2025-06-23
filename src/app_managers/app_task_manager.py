import time

from datetime import datetime, timedelta
from typing import Any, TYPE_CHECKING

from kivy.clock import Clock
from kivy.event import EventDispatcher

from managers.device.device_manager import DM
from managers.tasks.task import Task, TaskGroup

from src.utils.wrappers import log_time
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
    FIRST_TASK_MESSAGE = "No upcomming Tasks!\n\nPress + to add a new one,\nor select a Task to edit or delete."

    def __init__(self, app: "TaskApp"):
        super().__init__()
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.expiry_manager: "AppExpiryManager" = app.expiry_manager
        self.communication_manager: "AppCommunicationManager" = None  # connected in main.py

        # Task file - validated by ExpiryManager
        self.task_file_path: str = DM.PATH.TASK_FILE
        
        # Remove old task groups
        # Need to schedule daily
        self.expiry_manager._remove_old_task_groups()

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
    
    @log_time("get_task_groups")
    def get_task_groups(self) -> list[TaskGroup]:
        """
        Loads all Tasks from the last TASK_HISTORY_DAYS days, which are grouped by date.
        Returns a list of sorted TaskGroup objects with sorted Tasks, earliest first.
        """
        try:
            data = self.expiry_manager.get_task_data()
            
            # Get earliest date to include
            earliest_date = datetime.now().date() - timedelta(days=self.expiry_manager.TASK_HISTORY_DAYS)
            task_groups = self._extract_task_data(data,
                                                  earliest_date)
            
            # Sort by date
            sorted_task_groups = sorted(task_groups, key=lambda x: x.date_str)
            return sorted_task_groups
        
        except Exception as e:
            logger.error(f"Error loading Task groups: {e}")
            return []
    
    def _extract_task_data(self, data: dict[str, list[dict[str, Any]]], earliest_date: datetime) -> list[Task]:
        """Extracts the Task data from the Task file."""
        task_groups = []
        for date_key, tasks_data in data.items():
            task_date = datetime.strptime(date_key, DM.DATE.DATE_KEY).date()
            # Only include dates in range
            if task_date >= earliest_date:
                # Sort by effective time
                tasks = [Task.to_class(task_data) for task_data in tasks_data]
                sorted_tasks = sorted(tasks, key=lambda x: x.timestamp)
                task_groups.append(TaskGroup(date_str=date_key, tasks=sorted_tasks))
        
        return task_groups
    
    def get_current_task_group(self, task: Task | None = None) -> TaskGroup | None:
        """
        Gets the current TaskGroup, the TaskGroup of the given Task or the welcome TaskGroup.
        """
        # No TaskGroups
        if not self.task_groups:
            self._set_welcome_task_group()
            return self.task_groups[0]

        # Get nearest future TaskGroup
        if task is None:
            for task_group in self.task_groups:
                if task_group.date_str >= datetime.now().date().isoformat():
                    return task_group
            # No upcoming TaskGroups
            self._set_welcome_task_group()
            return self.task_groups[0]
            
        # Get Task's TaskGroup
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
        # Update HomeScreen
        self.update_home_after_changes(task.get_date_key())
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)

        Clock.schedule_once(lambda dt: self.app.get_screen(DM.SCREEN.HOME).scroll_to_task(task), 0.15)
        logger.debug(f"Added Task: {DM.get_task_log(task)}")

    def update_task(self, task_id: str, message: str, timestamp: datetime,
                    alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Updates existing Task by its ID.
        Updates task_groups, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Error updating Task, {DM.get_task_id_log(task_id)} not found")
            return
        
        self._edit_task_in_groups(task, message, timestamp, alarm_name, vibrate, keep_alarming)
        self.save_task_groups()
        
        # Refresh ExpiryManager
        self.expiry_manager._refresh_tasks()
        # Update HomeScreen
        self.update_home_after_changes(task.get_date_key())
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)
        
        Clock.schedule_once(lambda dt: self.app.get_screen(DM.SCREEN.HOME).scroll_to_task(task), 0.15)
        logger.debug(f"Updated Task: {DM.get_task_log(task)}")

    def delete_task(self, task_id: str) -> None:
        """
        Deletes a Task by ID.
        Updates task_groups, saves the Task to file,
         dispatches an event to update the Task display.
        """
        task = self.get_task_by_id(task_id)
        date_key = task.get_date_key()
        if not task:
            logger.error(f"Error deleting Task, {DM.get_task_id_log(task_id)} not found")
            return
        
        # Scroll to old pos if TaskGroup is still displayed
        self.scroll_to_old_pos()
        
        # Remove from TaskGroups
        self._remove_from_task_groups(task)
        self.save_task_groups()
        
        # Refresh ExpiryManager
        self.expiry_manager._refresh_tasks()
        # Update HomeScreen
        self.update_home_after_changes(date_key)
        # Refresh ServiceExpiryManager
        self.communication_manager.send_action(DM.ACTION.UPDATE_TASKS)

        logger.debug(f"Deleted Task: {DM.get_task_log(task)}")
    
    def _edit_task_in_groups(self, task: Task, message: str, timestamp: datetime,
                            alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Directly edits a Task's attributes in the TaskGroups.
        Only moves the Task between groups if the date has changed.
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
    
    def save_task_groups(self) -> None:
        """
        Saves the Task groups to the file.
        """
        try:
            # Format TaskGroups
            tasks_json = {}
            for task_group in self.task_groups:
                tasks_json[task_group.date_str] = [task.to_json() for task in task_group.tasks]
            
            self.expiry_manager.save_task_file(tasks_json)
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
                # Find Task by ID
                for j, group_task in enumerate(task_group.tasks):
                    if group_task.task_id == task.task_id:
                        task_group.tasks.pop(j)
                        
                        # If last Task in group, remove it
                        if not task_group.tasks:
                            self.task_groups.pop(i)
                        
                        return
                break
        else:
            logger.error(f"Error removing Task from TaskGroups, {DM.get_task_log(task)} not found")
    
    def refresh_task_groups(self) -> None:
        """
        Refreshes the Task groups.
        """
        logger.critical("Refreshing Task groups")
        self.task_groups = self.get_task_groups()
    
    def go_to_prev_task_group(self) -> None:
        """
        Gets the previous TaskGroup.
        """
        for i, task_group in enumerate(self.task_groups):
            if task_group.date_str == self.current_task_group.date_str:
                if i > 0:
                    self.update_home_after_changes(self.task_groups[i - 1].date_str)
                return
    
    def go_to_next_task_group(self) -> TaskGroup | None:
        """
        Gets the next TaskGroup.
        """
        for task_group in self.task_groups:
            if task_group.date_str > self.current_task_group.date_str:
                self.update_home_after_changes(task_group.date_str)
                return
    
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
    
    def get_task_by_id(self, task_id: str) -> Task | None:
        """
        Gets a Task by its ID.
        """
        for task_group in self.task_groups:
            for task in task_group.tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def get_task_by_timestamp(self, target_datetime: datetime) -> Task | None:
        """
        Get a Task object by its timestamp.
        Compares hours and minutes, ignoring seconds and microseconds.
        """
        target_date_key = target_datetime.strftime(DM.DATE.DATE_KEY)
        target_time = target_datetime.time()
        
        # Find TaskGroup for this date
        for task_group in self.task_groups:
            if task_group.date_str == target_date_key:
                # Check for match
                for task in task_group.tasks:
                    hour = task.timestamp.time().hour
                    minute = task.timestamp.time().minute
                    if hour == target_time.hour and minute == target_time.minute:
                        return task
                break
        
        return None
    
    def date_is_taken(self, target_datetime: datetime) -> bool:
        """
        Check if a date and time is taken by any Task.
        Compares hours and minutes, ignoring seconds and microseconds.
        """
        target_date_key = target_datetime.strftime(DM.DATE.DATE_KEY)
        target_time = target_datetime.time()
        
        # Find the TaskGroup for this date
        for task_group in self.task_groups:
            if task_group.date_str == target_date_key:
                # Check if conflict
                for task in task_group.tasks:
                    if task == self.task_to_edit:
                        continue

                    hour = task.timestamp.time().hour
                    minute = task.timestamp.time().minute
                    if hour == target_time.hour and minute == target_time.minute:
                        return True
                break
        
        return False

    def scroll_to_old_pos(self) -> None:
        """
        Records the current scroll position and date.
        Schedules to scroll to the old position.
        """
        old_pos = self.app.get_screen(DM.SCREEN.HOME).scroll_container.scroll_view.scroll_y
        old_date = self.app.get_screen(DM.SCREEN.HOME).task_manager.current_task_group.date_str
        Clock.schedule_once(lambda dt: self.app.get_screen(DM.SCREEN.HOME).scroll_to_pos_on_date(old_pos, old_date), 0.15)
    
    def _connect_communication_manager(self, communication_manager: "AppCommunicationManager") -> None:
        """Connects the CommunicationManager to the TaskManager."""
        self.communication_manager = communication_manager
