import json
import os

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass  # type: ignore

from service.service_task_manager import ServiceTaskManager

from service.utils import ACTION, PATH


AndroidNotificationManager = autoclass("android.app.NotificationManager")
AndroidString = autoclass("java.lang.String")
BuildVersion = autoclass("android.os.Build$VERSION")
Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
NotificationCompatBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
PendingIntent = autoclass("android.app.PendingIntent")
PythonActivity = autoclass("org.kivy.android.PythonActivity")
PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass('android.app.Service')


class BGTaskServiceManager:
    """Manages the background service functionality"""
    
    def __init__(self):
        self.notification_manager = None  # Initialized in service loop
        self.service_task_manager = ServiceTaskManager()

        self._running = True

        self.service_flag_file = PATH.SERVICE_FLAG
        
        self._has_notified = False
    
    def init_notification_manager(self):
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            from service.notification_manager import NotificationManager  # type: ignore
            self.notification_manager = NotificationManager(PythonService.mService)
    
    def handle_action(self, intent_or_action):
        """Handle notification actions"""
        if not self.service_task_manager.current_task:
            print("BGTaskService: No current task to handle action for")
            return Service.START_STICKY

        # Check if we received an intent or just an action string
        action = None
        if isinstance(intent_or_action, str):
            action = intent_or_action
            print(f"BGTaskService: Received string action: {action}")
        else:
            # Try to get the action from intent directly and then extras
            try:
                # First try to get it from the action field
                intent_action = intent_or_action.getAction()
                if intent_action:
                    action = intent_action
                    print(f"BGTaskService: Got action from intent action: {action}")
                
                # If that fails, try from extras
                elif intent_or_action.hasExtra("action"):
                    action = intent_or_action.getStringExtra("action")
                    print(f"BGTaskService: Got action from intent extra: {action}")
                
                else:
                    print("BGTaskService: Intent has no action field or extra")
            except Exception as e:
                print(f"BGTaskService: Error getting action from intent: {e}")
                return Service.START_STICKY

        if not action:
            print("BGTaskService: No action found to handle")
            return Service.START_STICKY

        print(f"BGTaskService: Handling action: {action}")
        
        # Cancel all notifications before handling the action
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        if action.endswith(ACTION.SNOOZE_A):
            # Snooze for 1 minute
            self.service_task_manager.snooze_task(action)
            self._has_notified = False
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action.endswith(ACTION.STOP):
            # Cancel the current Task
            self.service_task_manager.cancel_task()
            self._has_notified = False
            print("BGTaskService: Task cancelled")
            # Only stop if there's no current task
            if self.service_task_manager.current_task is None:
                self._running = False
                return Service.START_NOT_STICKY
            return Service.START_STICKY
        else:
            print(f"BGTaskService: Unknown action: {action}")
        
        return Service.START_STICKY
    
    def run_service(self):
        """
        Main service loop.
        - Checks if the service should stop (user opened the app)
        - Checks if the Task is expired
        - If the Task is expired, show notification.
          Otherwise, sleeps for WAIT_TIME seconds.
        """
        print(f"BGTaskService: Current Task expiry: {self.service_task_manager.current_task.timestamp}")

        while self._running and self.service_task_manager.current_task is not None:
            if self._should_stop_service():
                print("BGTaskService: Stop flag detected, stopping service")
                break
            
            if self.service_task_manager.is_task_expired() and not self._has_notified:
                print("BGTaskService: Task expired, showing notification")
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
                print(f"BGTaskService: Error removing stop flag: {e}")
    
    def _show_startup_notification(self):
        """Shows the initial foreground notification"""
        self.notification_manager.show_foreground_notification(
            "Task Monitor Active",
            "Watching for expired Tasks..."
        )


if __name__ == "__main__":
    print("BGTaskService: Starting background service")
    
    service_manager = BGTaskServiceManager()
    service_manager.remove_stop_flag()
    
    # Register broadcast receiver for actions
    try:
        context = PythonService.mService.getApplicationContext()
        package_name = context.getPackageName()
        
        # Create broadcast receiver
        def on_receive(context, intent):
            try:
                action = intent.getAction()
                if action:
                    # Strip package name from action
                    pure_action = action.split(".")[-1]
                    print(f"BGTaskService: Received broadcast action: {pure_action}")
                    service_manager.handle_action(pure_action)
            except Exception as e:
                print(f"BGTaskService: Error in broadcast receiver: {e}")
        
        # Create receiver with actions
        actions = [
            f"{package_name}.{ACTION.SNOOZE_A}",
            f"{package_name}.{ACTION.STOP}"
        ]
        receiver = BroadcastReceiver(
            on_receive,
            actions=actions
        )
        
        # Start the receiver
        receiver.start()
        print("BGTaskService: Registered action broadcast receiver")
        
    except Exception as e:
        print(f"BGTaskService: Error setting up broadcast receiver: {e}")
    
    # Initialize service if we have a task
    if service_manager.service_task_manager.current_task is not None:
        service_manager.init_notification_manager()
        # Show the startup notification
        service_manager.notification_manager.show_foreground_notification(
            "Task Monitor Active",
            f"Monitoring task due at {service_manager.service_task_manager.current_task.timestamp}",
            with_buttons=True
        )
        print("BGTaskService: Starting main service loop")
        # Main loop
        service_manager.run_service()
        # Stop the receiver when service ends
        receiver.stop()
    else:
        # If no task, still show a notification but exit soon
        service_manager.init_notification_manager()
        service_manager.notification_manager.show_foreground_notification(
            "Task Monitor",
            "No tasks to monitor",
            with_buttons=False
        )
    
    print("BGTaskService: Service stopping")
