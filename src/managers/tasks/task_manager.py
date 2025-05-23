import json
import time

from datetime import datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

from src.managers.device.device_manager import DM
from src.managers.settings_manager import SettingsManager
from src.managers.tasks.task_manager_utils import Task

from src.utils.background_service import notify_service_of_tasks_update
from src.utils.logger import logger

from src.settings import PATH, DATE


class TaskManager(EventDispatcher):
    """
    Manages Tasks and their storage using JSON.
    """
    def __init__(self):
        super().__init__()
        self.navigation_manager = App.get_running_app().navigation_manager
        if DM.is_android:
            self.settings_manager = SettingsManager()
        # Events
        self.register_event_type("on_task_saved_scroll_to_task")
        self.register_event_type("on_tasks_changed_update_task_display")
        self.register_event_type("on_task_edit_load_task_data")
        self.register_event_type("on_tasks_expired_set_date_expired")
        self.register_event_type("on_task_expired_trigger_alarm")
        self.register_event_type("on_task_expired_show_task_popup")
        self.register_event_type("on_task_cancelled_stop_alarm")

        # File path
        self.task_file_path: str = DM.get_storage_path(PATH.TASK_FILE)
        DM.validate_file(self.task_file_path)

        # Tasks
        self.tasks_by_date: dict[str, list[Task]] = self._load_tasks_by_date()
        self.sorted_active_tasks: list[dict] = None

        # New/Edit Task attributes
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None
        self.selected_vibrate: bool = False
        self.selected_keep_alarming: bool = False
        # Editing Task attributes
        self.task_to_edit: Task | None = None

        # Alarm attributes
        self.snooze_time: int = 60
        self._checked_background_cancelled_tasks: bool = False
        Clock.schedule_interval(self.check_task_expired, 1)
    
    def _load_tasks_by_date(self) -> dict[str, list[Task]] | dict:
        """
        Loads all Tasks from file, which are grouped by date.
        Returns a dictionary of date keys and lists of Task objects.
        """
        start_time = time.time()
        try:
            with open(self.task_file_path, "r") as f:
                data = json.load(f)
            
            tasks_by_date = {}
            for date_key, tasks_data in data.items():
                tasks_by_date[date_key] = []
                for task_data in tasks_data:
                    task = Task.to_class(task_data)
                    tasks_by_date[date_key].append(task)
            
            logger.trace(f"_load_tasks_by_date time: {time.time() - start_time:.4f}")
            return tasks_by_date
        
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            return {}
    
    def sort_active_tasks(self) -> None:
        """
        Takes the tasks_by_date dictionary and returns a list of Tasks sorted by date [earliest first].
        Looks at ALL tasks because snoozing could move a task to any future date.
        Includes:
        - All non-expired tasks (regardless of date)
        - Expired tasks from today and yesterday
        Used by HomeScreen's update_task_display to display all active Tasks.
        Only called on initial load and after Task add/edit/delete.
        """
        sorted_active_tasks = []
        now = datetime.now().replace(second=0, microsecond=0)
        yesterday = (now - timedelta(days=1)).date()
        today = now.date()
        
        # Look at ALL tasks in tasks_by_date
        for date_key, tasks in self.tasks_by_date.items():
            task_date = datetime.strptime(date_key, "%Y-%m-%d").date()
            
            # Keep all non-expired tasks, and expired tasks from today/yesterday
            active_tasks = [
                task for task in tasks 
                if not task.expired or task_date in (today, yesterday)
            ]
            
            if active_tasks:
                # Sort tasks within each date group by effective time (earliest first)
                sorted_tasks = sorted(active_tasks, 
                                    key=lambda task: task.timestamp + timedelta(seconds=task.snooze_time))
                
                # Use effective time for date string
                first_task = sorted_tasks[0]
                effective_date = Task.to_date_str(first_task.timestamp + timedelta(seconds=first_task.snooze_time))
                
                sorted_active_tasks.append({
                    "date": effective_date,
                    "tasks": sorted_tasks
                })
        
        # Sort by effective time (earliest first)
        sorted_active_tasks.sort(
            key=lambda x: (x["tasks"][0].timestamp + timedelta(seconds=x["tasks"][0].snooze_time)) 
            if x["tasks"] else datetime.max
        )
        
        if not sorted_active_tasks:
            start_task = Task(
                timestamp=(now - timedelta(minutes=1)).replace(second=0, microsecond=0),
                message="No upcoming tasks!\nPress + to add a new one.",
                expired=True
            )
            sorted_active_tasks.append({
                "date": start_task.get_date_str(),
                "tasks": [start_task]
            })
        
        self.sorted_active_tasks = sorted_active_tasks

    def _save_tasks_to_json(self) -> bool:
        """
        Saves all Tasks to the PATH.TASK_FILE file, grouped by date.
        Returns True if successful, False otherwise.
        Called by save_all_tasks with a delay.
        Only called on Task add/edit/delete.
        """
        start_time = time.time()
        try:
            tasks_json = {}
            # Group by date
            for date_key, tasks in self.tasks_by_date.items():
                tasks_json[date_key] = [task.to_json() for task in tasks]
            
            with open(self.task_file_path, "w") as f:
                json.dump(tasks_json, f, indent=2)
            
            logger.error(f"save_tasks_to_json time: {time.time() - start_time:.4f}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving tasks to file: {e}")
            return False
    
    def add_task(self, message: str, timestamp: datetime,
                 alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Adds Task to tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = Task(message=message, timestamp=timestamp,
                    alarm_name=alarm_name, vibrate=vibrate, keep_alarming=keep_alarming,
                    snooze_time=0)
        
        # Round timestamp
        task.timestamp = task.timestamp.replace(second=0, microsecond=0)
        
        # Get date key and add to appropriate date group
        date_key = task.get_date_key()
        if date_key not in self.tasks_by_date:
            self.tasks_by_date[date_key] = []
        self.tasks_by_date[date_key].append(task)

        # Save, reload and notify service
        self._save_tasks_to_json()
        self._reload_tasks()
        notify_service_of_tasks_update()

        # Notify to update the Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved_scroll_to_task", task=task), 0.1)
    
    def update_task(self, task_id: str, message: str, timestamp: datetime,
                    alarm_name: str, vibrate: bool, keep_alarming: bool) -> None:
        """
        Updates existing Task by its ID.
        Updates tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display and scroll to the Task.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found for update")
            return
        
        old_date_key = task.get_date_key()
        
        # Update task properties with full precision timestamp
        task.timestamp = timestamp
        task.message = message
        task.alarm_name = alarm_name
        task.vibrate = vibrate
        task.keep_alarming = keep_alarming
        task.snooze_time = 0

        # Update expired state using rounded timestamps
        now = datetime.now().replace(second=0, microsecond=0)
        now += timedelta(seconds=1)
        if timestamp > now and task.expired:
            # Task from past to future, -> not expired
            task.expired = False
        elif timestamp <= now and not task.expired:
            # Task from future to past, -> expired
            task.expired = True
        
        # If date will change, move Task to new date group
        new_date_key = task.get_date_key()
        
        # If date changed, move Task to new date group
        if old_date_key != new_date_key:
            # Remove from old date group
            if old_date_key in self.tasks_by_date:
                self.tasks_by_date[old_date_key].remove(task)
                # Remove empty date groups
                if not self.tasks_by_date[old_date_key]:
                    del self.tasks_by_date[old_date_key]
            
            # Add to new date group
            if new_date_key not in self.tasks_by_date:
                self.tasks_by_date[new_date_key] = []
            self.tasks_by_date[new_date_key].append(task)

        # Save, reload and notify service
        self._save_tasks_to_json()
        self._reload_tasks()
        notify_service_of_tasks_update()
        
        task = self.get_task_by_id(task_id)
        # Notify to update the Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
        # Notify to scroll to Task
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved_scroll_to_task", task=task), 0.1)

    def delete_task(self, task_id: str) -> None:
        """
        Deletes a Task by ID.
        Updates tasks_by_date, saves the Task to file,
         dispatches an event to update the Task display.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found")
            return
        
        # Save copy before deletion for notification
        date_key = task.get_date_key()
        # Remove from memory
        if date_key in self.tasks_by_date and task in self.tasks_by_date[date_key]:
            self.tasks_by_date[date_key].remove(task)
            # Remove empty date groups
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
        
        self._save_tasks_to_json()
        self._reload_tasks()
        notify_service_of_tasks_update()
        
        # Notify to update Task display
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
    
    def snooze_task(self, task_id: str) -> None:
        """Snooze a Task by ID."""
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task with id {task_id} not found for snooze")
            return
        
        snooze_seconds = task.snooze_time + self.snooze_time
        new_timestamp = task.timestamp + timedelta(seconds=snooze_seconds)
        
        # Check for overlaps
        while self._has_time_overlap(new_timestamp):
            logger.debug(f"Task {task.task_id} would overlap with another task, adding 10 seconds")
            snooze_seconds += self.snooze_time
            new_timestamp = task.timestamp + timedelta(seconds=snooze_seconds)
        
        # Update task properties
        task.snooze_time = snooze_seconds
        task.expired = False
        
        self._save_tasks_to_json()
        self._reload_tasks()
        notify_service_of_tasks_update()
        
        # Update UI
        self.dispatch("on_tasks_changed_update_task_display", modified_task=task)
        Clock.schedule_once(lambda dt: self.dispatch("on_task_saved_scroll_to_task", task=task), 0.1)
    
    def _has_time_overlap(self, timestamp: datetime) -> bool:
        """Checks if the snoozed Task or current Task would overlap with another Task."""
        for task_group in self.sorted_active_tasks:
            for task in task_group["tasks"]:
                if task.timestamp + timedelta(seconds=task.snooze_time) == timestamp:
                    return True
        
        return False

    def _reload_tasks(self) -> None:
        """Reload all tasks from file and update everything"""
        # Reload tasks from file
        self.tasks_by_date = self._load_tasks_by_date()
        # Resort active tasks
        self.sort_active_tasks()

    def _save_task_changes(self, task_id: str, changes: dict) -> None:
        """Saves Task changes to file"""
        try:
            # Use _load_tasks_by_date to get current task data
            task_data = {}
            for date_key, tasks in self.tasks_by_date.items():
                task_data[date_key] = [task.to_json() for task in tasks]
                
                # Update the specific task if found
                for task in task_data[date_key]:
                    if task["task_id"] == task_id:
                        task.update(changes)
                        # Save the updated data
                        with open(self.task_file_path, "w") as f:
                            json.dump(task_data, f, indent=2)
                        
                        logger.debug(f"Saved changes for Task {task_id}: {changes}")
                        
                        # Reload all tasks to ensure sync
                        self.tasks_by_date = self._load_tasks_by_date()
                        self.sort_active_tasks()
                        return
            
            logger.error(f"Task {task_id} not found in task data")
        
        except Exception as e:
            logger.error(f"Error saving Task changes: {e}")
    
    def set_expired_tasksbydate(self) -> None:
        """
        Set Tasks to be expired if their timestamp is in the past.
        Checks first active Task group and sets each Tasks expired state.
        If changes, save to memory and file.
        If all Tasks in group are now expired, notify to update Task's appearance.
        """
        try:
            active_tasks = self.sorted_active_tasks[0]
        except IndexError:
            return
        
        if not active_tasks:
            return
        

        if all(task.expired for task in active_tasks["tasks"]):
                self.dispatch("on_tasks_expired_set_date_expired", 
                                      date=active_tasks["date"])
                self.dispatch("on_tasks_changed_update_task_display") 
    
    def get_task_by_timestamp(self, target_datetime: datetime) -> Task | None:
        """
        Get a Task object by its timestamp.
        Only compares date and hours/minutes, ignoring seconds and microseconds.
        """
        target_date_key = target_datetime.strftime(DATE.DATE_KEY)
        target_time = target_datetime.time()
        
        # First check if we have any tasks on this date
        if target_date_key not in self.tasks_by_date:
            return None
        
        # Then check for time match on that date
        for task in self.tasks_by_date[target_date_key]:
            task_time = task.timestamp.time()
            if task_time.hour == target_time.hour and task_time.minute == target_time.minute:
                return task
        
        return None
    
    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a Task object by its ID."""
        for date_key, tasks in self.tasks_by_date.items():
            for task in tasks:
                if task.task_id == task_id:
                    return task
        
        return None
    
    def date_is_taken(self, target_datetime: datetime) -> bool:
        """
        Check if a date and time is taken by any Task.
        First checks the date to avoid unnecessary time comparisons.
        Only compares hours and minutes, ignoring seconds and microseconds.
        """
        target_date_key = target_datetime.strftime(DATE.DATE_KEY)
        
        # First check if we have any tasks on this date
        if target_date_key not in self.tasks_by_date:
            return False
        
        # Then check for time conflicts on that date, comparing only hours and minutes
        target_time = target_datetime.time()
        for task in self.tasks_by_date[target_date_key]:
            task_time = task.timestamp.time()
            if task_time.hour == target_time.hour and task_time.minute == target_time.minute:
                return True
        
        return False

    def check_task_expired(self, dt: float) -> None:
        """
        Check if any Tasks are expired and trigger the alarm if so.
        Compares rounded timestamps (to the minute) for consistent timing.
        """
        if not self._checked_background_cancelled_tasks:
            self.check_background_cancelled_tasks()
            self._checked_background_cancelled_tasks = True
            return

        if not self.sorted_active_tasks:
            return
        
        now = datetime.now().replace(second=0, microsecond=0)
        
        # Check ALL task groups, not just the first one
        for task_group in self.sorted_active_tasks:
            for task in task_group["tasks"]:
                # Skip already expired tasks
                if task.expired:
                    continue
                    
                # Calculate effective time (timestamp + snooze)
                effective_time = task.timestamp + timedelta(seconds=task.snooze_time)
                if effective_time <= now:
                    task.expired = True
                    self.set_expired_tasksbydate()
                    self._save_tasks_to_json()
                    self._reload_tasks()
                    notify_service_of_tasks_update()
                    self.dispatch("on_task_expired_trigger_alarm", task=task)
                    # Trigger popup
                    self.dispatch("on_task_expired_show_task_popup", task=task)
                    return
    
    def check_background_cancelled_tasks(self, *args, **kwargs) -> None:
        """
        Check if there were tasks that were cancelled via notification.
        Handles both alarm cancellation and popup display.
        """
        logger.critical("Checking for background cancelled tasks")
        if not DM.is_android:
            return
        
        # If user interacted through notification, stop alarm and show popup
        cancelled_task_id = self.settings_manager.get_cancelled_task_id()
        if cancelled_task_id:
            task = self.get_task_by_id(cancelled_task_id)
            logger.critical(f"Found task: {task.task_id if task else None}")
            if task:
                self.dispatch("on_task_cancelled_stop_alarm")
                self.dispatch("on_task_expired_show_task_popup", task=task)
            
            Clock.schedule_once(lambda dt: self.settings_manager.clear_cancelled_task_id(), 5)

    def on_task_saved_scroll_to_task(self, task, *args):
        """Default handler for on_task_saved_scroll_to_task event"""
        pass
    
    def on_tasks_changed_update_task_display(self, *args, **kwargs):
        """Default handler for on_tasks_changed_update_task_display event"""
        pass
    
    def on_task_edit_load_task_data(self, *args, **kwargs):
        """Default handler for on_task_edit_load_task_data event"""
        pass
    
    def on_tasks_expired_set_date_expired(self, *args, **kwargs):
        """Default handler for on_tasks_expired_set_date_expired event"""
        pass
    
    def on_task_expired_trigger_alarm(self, *args, **kwargs):
        """Default handler for on_task_expired_trigger_alarm event"""
        pass

    def on_task_expired_show_task_popup(self, *args, **kwargs):
        """Default handler for on_task_expired_show_task_popup event"""
        pass

    def on_task_cancelled_stop_alarm(self, *args, **kwargs):
        """Default handler for on_task_cancelled_stop_alarm event"""
        pass
