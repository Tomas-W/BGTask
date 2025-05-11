import time

from jnius import autoclass  # type: ignore

from service.service_logger import logger
from service.service_task_manager import ServiceTaskManager
from service.utils import ACTION, get_service_timestamp

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass('android.app.Service')


class ServiceManager:
    """
    Manages the Android background service and Task monitoring, it:
    - Monitors the current Task for expiration
    - Handles task actions (snooze, cancel) from notifications
    - Continuous background operation with proper resource management
    """
    def __init__(self):
        self.notification_manager = None  # Initialized in service loop
        self.service_task_manager = ServiceTaskManager()
        self._running = True
        self._need_foreground_update = True
    
    def init_notification_manager(self):
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            from service.service_notification_manager import ServiceNotificationManager  # type: ignore
            self.notification_manager = ServiceNotificationManager(PythonService.mService)
    
    def handle_action(self, action: str):
        """
        Handles notification button actions from foreground or Task notifications.
        Always returns START_STICKY to ensure the service keeps running.
        """
        if not self.service_task_manager.current_task:
            logger.debug("No current task to handle action for")
            return Service.START_STICKY

        # Cancel all notifications
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        if action.endswith(ACTION.SNOOZE_A):
            self.service_task_manager.snooze_task(action)
            self._need_foreground_update = True
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action.endswith(ACTION.CANCEL):
            self.service_task_manager.cancel_task()
            logger.debug("Task cancelled")
            self._need_foreground_update = True
            # Keep service running with START_STICKY
            return Service.START_STICKY
        else:
            logger.error(f"Unknown action: {action}")
        
        return Service.START_STICKY
    
    def update_foreground_notification(self) -> None:
        """Updates the foreground notification with the current Task's expiry time"""
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

    def force_foreground_notification(self) -> None:
        """Ensures the foreground notification is active with current task info"""
        if not self.notification_manager:
            return
            
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

    def run_service(self):
        """
        Main service loop.
        - Ensures foreground notification is always active
        - Checks for foreground notification updates
        - Checks if the Task is expired
        - If the Task is expired, show notification and get next Task.
        """
        logger.debug("Starting main service loop")
        log_tick = 0
        while self._running:
            
            # Ensure foreground notification is active
            self.force_foreground_notification()
            

            # Update foreground notification if needed
            if self._need_foreground_update:
                self.update_foreground_notification()
            
            # Check for expired Task
            if self.service_task_manager.current_task is not None:
                if self.service_task_manager.is_task_expired():
                    logger.debug("Task expired, showing notification")
                    self.notification_manager.show_task_notification(
                        "Task Expired",
                        self.service_task_manager.current_task.message
                    )
                    # Add to monitoring and get next task
                    self.service_task_manager.handle_expired_task()
                    # Update foreground notification
                    self._need_foreground_update = True
            
            log_tick += 1
            if log_tick % 120 == 0:
                task = self.service_task_manager.current_task if self.service_task_manager.current_task else None
                task_log = task.timestamp if task else "No task"
                logger.debug(f"Service check for {task_log}")
            time.sleep(0.5)
