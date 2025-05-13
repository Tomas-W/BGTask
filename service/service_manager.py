import time
import os

from jnius import autoclass  # type: ignore
from typing import TYPE_CHECKING

from src.managers.tasks.task_manager_utils import Task
from src.managers.settings_manager import SettingsManager

from service.service_audio_manager import ServiceAudioManager
from service.service_logger import logger
from service.service_task_manager import ServiceTaskManager
from service.service_utils import ACTION, get_service_timestamp, PATH

if TYPE_CHECKING:
    from service.service_notification_manager import ServiceNotificationManager

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")
Intent = autoclass("android.content.Intent")
Context = autoclass("android.content.Context")
RunningAppProcessInfo = autoclass("android.app.ActivityManager$RunningAppProcessInfo")


SERVICE_SLEEP_TIME = 0.5
CHECK_TASK_REFRESH_TICK = 6

class ServiceManager:
    """
    Manages the Android background service and Task monitoring, it:
    - Monitors the current Task for expiration
    - Handles task actions (snooze, cancel) from notifications
    - Continuous background operation with proper resource management
    """
    def __init__(self):
        self.notification_manager: "ServiceNotificationManager | None" = None  # Initialized in service loop
        self.service_task_manager: ServiceTaskManager = ServiceTaskManager()
        self.audio_manager: ServiceAudioManager = ServiceAudioManager()
        self.settings_manager = None

        # Loop variables
        self._running: bool = True
        self._need_foreground_update: bool = True
        self._tasks_changed_flag: str = PATH.TASKS_CHANGED_FLAG

        # ActivityManager
        self._app_package_name = None
        self._activity_manager = None
        self._init_activity_manager()
    
    def run_service(self) -> None:
        """
        Main service loop.
        - Ensures foreground notification is always active
        - Updates Tasks when app's on_pause has set a flag file
        - Checks for foreground notification updates
        - Checks if the Task is expired
        - If the Task is expired, show notification and get next Task.
        """
        logger.debug("Starting main service loop")
        
        # Initialize settings after a small delay to ensure service context is ready
        time.sleep(0.5)
        self._init_settings_manager()
        
        update_task_tick = 0
        while self._running:
            # Always show foreground notification
            self.force_foreground_notification_display()
            
            # Check if app is in foreground
            if self.is_app_in_foreground():
                # If app is in foreground, stop any alarms and skip task monitoring
                self.audio_manager.stop_alarm_vibrate()
                time.sleep(SERVICE_SLEEP_TIME)
                continue
            
            # Rest of the service loop (only runs when app is in background)
            # Perioducally check for flag file
            # if found: update Tasks and foreground notification
            update_task_tick += 1
            if update_task_tick >= CHECK_TASK_REFRESH_TICK:
                update_task_tick = 0
                if self.need_tasks_update():
                    self._need_foreground_update = True
            
            # If a Task is updated or expired, update the foreground notification
            if self._need_foreground_update:
                self.update_foreground_notification_info()
            
            # No current Task
            if not self.service_task_manager.current_task:
                time.sleep(SERVICE_SLEEP_TIME)
                continue

            # No expired Task
            if not self.service_task_manager.is_task_expired():
                time.sleep(SERVICE_SLEEP_TIME)
                continue

            logger.debug("Task expired, showing notification")
            # Clean up any previously expired Task
            if self.service_task_manager.expired_task:
                self.clean_up_previous_task()
            
            # Process newly expired Task
            expired_task = self.service_task_manager.handle_expired_task()
            if expired_task:
                self.notify_user_of_expiry(expired_task)
            
            self._need_foreground_update = True
            time.sleep(SERVICE_SLEEP_TIME)
        
        self.audio_manager.stop_alarm_vibrate()
    
    def force_foreground_notification_display(self) -> None:
        """Ensures the foreground notification is displayed with current Task info"""
        if self.service_task_manager.current_task:
            time_label = get_service_timestamp(self.service_task_manager.current_task)
            message = self.service_task_manager.current_task.message
            with_buttons = True
        
        else:
            time_label = "No tasks to monitor"
            message = ""
            with_buttons = False
            
        self.notification_manager.ensure_foreground_notification(
            time_label,
            message,
            with_buttons
        )
    
    def is_app_in_foreground(self) -> bool:
        """Check if our app is in the foreground"""
        try:
            if not self._activity_manager or not self._app_package_name:
                return False
                
            # Get running app processes
            running_apps = self._activity_manager.getRunningAppProcesses()
            if not running_apps:
                return False
                
            # Check if our app is in foreground
            for process in running_apps:
                if (process.processName == self._app_package_name and 
                    process.importance == RunningAppProcessInfo.IMPORTANCE_FOREGROUND):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking app state: {e}")
            return False
    
    def need_tasks_update(self) -> bool:
        """
        Checks if the main app has set the tasks changed flag
        If so, updates Tasks, removes the flag file and returns True
        """
        if self._task_flag_exists():
            logger.debug("Found tasks changes flag, updating tasks")
            self._refresh_active_tasks()
            self._remove_task_flag()
            return True
        
        return False
    
    def _task_flag_exists(self) -> bool:
        return os.path.exists(self._tasks_changed_flag)
    
    def _remove_task_flag(self) -> None:
        try:
            if os.path.exists(self._tasks_changed_flag):
                os.remove(self._tasks_changed_flag)
        except Exception as e:
            logger.error(f"Error removing tasks flag file: {e}")
    
    def _refresh_active_tasks(self) -> None:
        """Refreshes the active Tasks"""
        self.service_task_manager.active_tasks = self.service_task_manager._get_active_tasks()
        new_task = self.service_task_manager.get_current_task()
        
        # If current Task is no longer closest, update it
        if (new_task and 
            ((not self.service_task_manager.current_task) or 
                (new_task.task_id != self.service_task_manager.current_task.task_id))):
            logger.debug(f"Found new task {new_task.task_id}, updating current task")
            self.service_task_manager.current_task = new_task
            self._need_foreground_update = True
    
    def clean_up_previous_task(self) -> None:
        """Cleans up the previous Task's alarm and notifications"""
        logger.debug("Stopping previous expired task")
        self.audio_manager.stop_alarm_vibrate()
        self.notification_manager.cancel_all_notifications()
        self.service_task_manager.cancel_task()
        self.service_task_manager.clear_expired_task()
    
    def notify_user_of_expiry(self, expired_task: Task) -> None:
        """
        Notify the user of the expiry of a Task by
         showing a notification and playing an alarm
        """
        self.notification_manager.show_task_notification(
                    "Task Expired",
                    expired_task.message
                )
        self.audio_manager.trigger_alarm(expired_task)
    
    def _init_notification_manager(self) -> None:
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            from service.service_notification_manager import ServiceNotificationManager  # type: ignore
            self.notification_manager = ServiceNotificationManager(PythonService.mService)
    
    def handle_action(self, action: str) -> int:
        """
        Handles notification button actions from foreground or Task notifications.
        Always returns START_STICKY to ensure the service keeps running.
        """
        if not self.service_task_manager.current_task and not self.service_task_manager.expired_task:
            logger.debug("No current task to handle action for")
            return Service.START_STICKY

        # Cancel all notifications
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        # Clicked Snooze button
        if action.endswith(ACTION.SNOOZE_A):
            self.service_task_manager.snooze_task(action)
            self.audio_manager.stop_alarm_vibrate()
            self._need_foreground_update = True
            return Service.START_REDELIVER_INTENT
        
        # Clicked Cancel button or swiped notification
        elif action.endswith(ACTION.CANCEL):
            # Store the task ID if we have an expired task
            # So in-app popup can be shown on app open
            if self.service_task_manager.expired_task:
                logger.debug(f"Storing cancelled task ID: {self.service_task_manager.expired_task.task_id}")
                if self.settings_manager:
                    self.settings_manager.set_cancelled_task_id(self.service_task_manager.expired_task.task_id)
                else:
                    logger.error("Settings manager not initialized, cannot store cancelled task ID")
            
            self.service_task_manager.cancel_task()
            self._need_foreground_update = True
            self.audio_manager.stop_alarm_vibrate()
            return Service.START_STICKY
        
        # Clicked notification to open app
        elif action.endswith(ACTION.OPEN_APP):
            self.service_task_manager.cancel_task()
            self._need_foreground_update = True
            self.audio_manager.stop_alarm_vibrate()
            self._open_app()
        
        else:
            logger.error(f"Unknown action: {action}")
            self.audio_manager.stop_alarm_vibrate()
            return Service.START_STICKY

    def _open_app(self) -> None:
        """Opens the app from Task notification"""
        try:
            context = self.notification_manager.context
            intent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName())
            if intent:
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                intent.addCategory("android.intent.category.LAUNCHER")
                context.startActivity(intent)
                logger.debug("Launched app activity")
        
        except Exception as e:
            logger.error(f"Error launching app: {e}")
    
    def update_foreground_notification_info(self) -> None:
        """Updates the foreground notification with the current Task's info"""
        if self.service_task_manager.current_task:
            time_label = get_service_timestamp(self.service_task_manager.current_task)
            message = self.service_task_manager.current_task.message
            self.notification_manager.show_foreground_notification(
                time_label,
                message,
                with_buttons=True
            )
        
        else:
            self.notification_manager.show_foreground_notification(
                "No tasks to monitor",
                "",
                with_buttons=False
            )
        
        self._need_foreground_update = False

    def _init_activity_manager(self) -> None:
        """Initialize ActivityManager and get package name"""
        try:
            context = PythonService.mService.getApplicationContext()
            self._activity_manager = context.getSystemService(Context.ACTIVITY_SERVICE)
            self._app_package_name = context.getPackageName()
            logger.debug("Initialized ActivityManager")
        
        except Exception as e:
            logger.error(f"Error initializing ActivityManager: {e}")
    
    def _init_settings_manager(self) -> None:
        """Initialize the SettingsManager with retries"""
        if self.settings_manager is None:
            try:
                # Try up to 3 times with 0.2s delay between attempts
                self.settings_manager = SettingsManager(max_retries=3, retry_delay=0.2)
                logger.debug("Successfully initialized SettingsManager")
            except Exception as e:
                logger.error(f"Error initializing SettingsManager after retries: {e}")
                # Don't raise here - we want the service to keep running even if settings fail
                # The service will retry settings initialization on next loop
