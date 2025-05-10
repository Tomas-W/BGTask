import time

from jnius import autoclass  # type: ignore

from service.service_logger import logger
from service.service_task_manager import ServiceTaskManager
from service.utils import ACTION, PATH, get_service_timestamp


PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass('android.app.Service')


class ServiceManager:
    """Manages the background service functionality"""
    
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
        Handles notification button actions from the foreground or Task notifications.
        Always returns START_STICKY to ensure the service keeps running.
        """
        if not self.service_task_manager.current_task:
            logger.debug("No current task to handle action for")
            return Service.START_STICKY

        # Cancel all notifications before handling the action
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        if action.endswith(ACTION.SNOOZE_A):
            self.service_task_manager.snooze_task(action)
            self._need_foreground_update = True
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action.endswith(ACTION.STOP):
            # Cancel the current Task
            self.service_task_manager.cancel_task()
            logger.debug("Task cancelled")
            self._need_foreground_update = True
            
            # Keep service running with START_STICKY
            return Service.START_STICKY
        else:
            logger.error(f"Unknown action: {action}")
        
        return Service.START_STICKY
    
    def update_foreground_notification(self) -> None:
        """Updates the foreground notification with the next task's expiry time"""
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

    def run_service(self):
        """
        Main service loop.
        - Checks if the Task is expired
        - If the Task is expired, show notification and get next task.
          Otherwise, sleeps for WAIT_TIME seconds.
        """
        log_tick = 0
        while self._running:
            
            # Update foreground notification if needed
            if self._need_foreground_update:
                self.update_foreground_notification()
            
            # Only check for expired tasks if we have a current task
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
