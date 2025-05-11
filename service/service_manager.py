import time

from jnius import autoclass  # type: ignore
from typing import TYPE_CHECKING

from src.managers.tasks.task_manager_utils import Task

from service.service_audio_manager import ServiceAudioManager
from service.service_logger import logger
from service.service_task_manager import ServiceTaskManager
from service.service_utils import ACTION, get_service_timestamp

if TYPE_CHECKING:
    from service.service_notification_manager import ServiceNotificationManager

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")
Intent = autoclass("android.content.Intent")
Context = autoclass("android.content.Context")


SERVICE_SLEEP_TIME = 0.5
SERVICE_REFRESH_TICK = 6

class ServiceManager:
    """
    Manages the Android background service and Task monitoring, it:
    - Monitors the current Task for expiration
    - Handles task actions (snooze, cancel) from notifications
    - Continuous background operation with proper resource management
    """
    def __init__(self):
        self.notification_manager: ServiceNotificationManager | None = None  # Initialized in service loop
        self.service_task_manager: ServiceTaskManager = ServiceTaskManager()
        self.audio_manager: ServiceAudioManager = ServiceAudioManager()

        self._running: bool = True
        self._need_foreground_update: bool = True
    
    def init_notification_manager(self) -> None:
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
            self.audio_manager.stop_alarm_vibrating()
            self._need_foreground_update = True
            return Service.START_REDELIVER_INTENT
        
        # Clicked Cancel button
        elif action.endswith(ACTION.CANCEL):
            self.service_task_manager.cancel_task()
            self._need_foreground_update = True
            self.audio_manager.stop_alarm_vibrating()
            return Service.START_STICKY
        
        # Clicked notification to open app
        elif action.endswith(ACTION.OPEN_APP):
            # Clean up task like we do for cancel
            self.service_task_manager.cancel_task()
            self._need_foreground_update = True
            self.audio_manager.stop_alarm_vibrating()
            
            # Launch the app
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
            
            return Service.START_STICKY
        
        else:
            logger.error(f"Unknown action: {action}")
            self.audio_manager.stop_alarm_vibrating()
        
        return Service.START_STICKY
    
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
        self.audio_manager.stop_alarm_vibrating()
        self.notification_manager.cancel_all_notifications()
        self.service_task_manager.cancel_task()
        self.service_task_manager.clear_expired_task()
    
    def update_tasks(self, update_task_tick: int) -> int:
        """Periodically refresh active tasks and return updated tick count"""
        update_task_tick += 1
        if update_task_tick >= SERVICE_REFRESH_TICK:
            update_task_tick = 0
            self._refresh_active_tasks()
        
        return update_task_tick
    
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
    
    def run_service(self) -> None:
        """
        Main service loop.
        - Ensures foreground notification is always active
        - Checks for foreground notification updates
        - Checks if the Task is expired
        - If the Task is expired, show notification and get next Task.
        """
        logger.debug("Starting main service loop")
        update_task_tick = 0
        while self._running:
            
            self.force_foreground_notification_display()

            # Periodically refresh active Tasks to pick up updates
            # This is needed for on_pause
            update_task_tick = self.update_tasks(update_task_tick)
            
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
        
        self.audio_manager.stop_alarm_vibrating()
