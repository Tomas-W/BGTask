import os

from jnius import autoclass  # type: ignore

from service.service_logger import logger
from service.service_task_manager import ServiceTaskManager
from service.utils import ACTION, PATH


PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass('android.app.Service')


class ServiceManager:
    """Manages the background service functionality"""
    
    def __init__(self):
        self.notification_manager = None  # Initialized in service loop
        self.service_task_manager = ServiceTaskManager()

        self.service_flag_file = PATH.SERVICE_FLAG
        self._has_notified = False

        self._running = True
    
    def init_notification_manager(self):
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            from service.notification_manager import NotificationManager  # type: ignore
            self.notification_manager = NotificationManager(PythonService.mService)
    
    def handle_action(self, intent_or_action):
        """Handle notification actions"""
        if not self.service_task_manager.current_task:
            logger.debug("BGTaskService: No current task to handle action for")
            return Service.START_STICKY

        # Check if we received an intent or just an action string
        action = None
        if isinstance(intent_or_action, str):
            action = intent_or_action
        else:
            # Try to get the action from intent directly and then extras
            try:
                # First try to get it from the action field
                intent_action = intent_or_action.getAction()
                if intent_action:
                    action = intent_action
                
                # If that fails, try from extras
                elif intent_or_action.hasExtra("action"):
                    action = intent_or_action.getStringExtra("action")
                                
                else:
                    logger.error("BGTaskService: Intent has no action field or extra")
            except Exception as e:
                logger.error(f"BGTaskService: Error getting action from intent: {e}")
                return Service.START_STICKY

        if not action:
            return Service.START_STICKY

        # Cancel all notifications before handling the action
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        if action.endswith(ACTION.SNOOZE_A):
            self.service_task_manager.snooze_task(action)
            self._has_notified = False
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action.endswith(ACTION.STOP):
            # Cancel the current Task
            self.service_task_manager.cancel_task()
            self._has_notified = False
            logger.debug("BGTaskService: Task cancelled")

            # Only stop if there's no current task
            if self.service_task_manager.current_task is None:
                self._running = False
                return Service.START_NOT_STICKY
            
            logger.debug(f"BGTaskService: Loaded new Task for {self.service_task_manager.current_task.timestamp}")
            
            return Service.START_STICKY
        else:
            logger.error(f"BGTaskService: Unknown action: {action}")
        
        return Service.START_STICKY
    
    def run_service(self):
        """
        Main service loop.
        - Checks if the service should stop (user opened the app)
        - Checks if the Task is expired
        - If the Task is expired, show notification.
          Otherwise, sleeps for WAIT_TIME seconds.
        """
        logger.debug(f"BGTaskService: Current Task expiry: {self.service_task_manager.current_task.timestamp}")

        while self._running and self.service_task_manager.current_task is not None:
            if self._should_stop_service():
                logger.debug("BGTaskService: Stop flag detected, stopping service")
                break
            
            if self.service_task_manager.is_task_expired() and not self._has_notified:
                logger.debug("BGTaskService: Task expired, showing notification")
                self.notification_manager.show_task_notification(
                    "Task Expired",
                    self.service_task_manager.current_task.message
                )
                self._has_notified = True
    
    def _should_stop_service(self):
        """Returns True if the service should stop"""
        return os.path.exists(self.service_flag_file)
    
    def remove_stop_flag(self):
        """Removes the stop flag if it exists"""
        if os.path.exists(self.service_flag_file):
            try:
                os.remove(self.service_flag_file)
            except Exception as e:
                logger.error(f"BGTaskService: Error removing stop flag: {e}")
