import json
import os
import time

from datetime import datetime, timedelta
from jnius import autoclass, cast   # type: ignore
from android.broadcast import BroadcastReceiver

# Constants
WAIT_TIME = 15  # seconds
SERVICE_FLAG_FILE = "app/src/assets/service_stop.flag"
SERVICE_TASK_FILE = "app/src/assets/first_task.json"

# Java classes
PythonActivity = autoclass("org.kivy.android.PythonActivity")
PythonService = autoclass("org.kivy.android.PythonService")
AndroidNotificationManager = autoclass("android.app.NotificationManager")
NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationCompatBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
BuildVersion = autoclass("android.os.Build$VERSION")
Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
PendingIntent = autoclass("android.app.PendingIntent")
AndroidString = autoclass("java.lang.String")
Service = autoclass('android.app.Service')

# Define notification actions and constants
class NotificationActions:
    """Constants for notification actions"""
    OPEN_APP = "open_app"
    SNOOZE = "snooze"
    CANCEL = "cancel"

    # Request codes for PendingIntents
    REQUEST_OPEN_APP = 1001
    REQUEST_SNOOZE = 1002
    REQUEST_CANCEL = 1003


class NotificationChannels:
    """Constants for notification channels"""
    FOREGROUND_SERVICE = "task_channel"
    EXPIRED_TASKS = "expired_task_channel"


class NotificationPriority:
    """Constants for notification priorities"""
    LOW = NotificationCompat.PRIORITY_LOW
    DEFAULT = NotificationCompat.PRIORITY_DEFAULT
    HIGH = NotificationCompat.PRIORITY_HIGH


class NotificationImportance:
    """Constants for notification channel importance"""
    DEFAULT = AndroidNotificationManager.IMPORTANCE_DEFAULT
    HIGH = AndroidNotificationManager.IMPORTANCE_HIGH


class BGTaskServiceManager:
    """Manages the background service functionality"""
    
    def __init__(self):
        # Initialized in service loop if there is a Task to monitor
        self.notification_manager = None

        self._running = True

        self.service_flag_file = self._get_storage_path(SERVICE_FLAG_FILE)
        self.service_task_file = self._get_storage_path(SERVICE_TASK_FILE)
        
        self._current_task = self._get_current_task()
        self._snooze_time = 0
        self._has_notified = False
    
    def init_notification_manager(self):
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            self.notification_manager = BGTaskNotificationManager()
    
    def handle_action(self, intent_or_action):
        """Handle notification actions"""
        if not self._current_task:
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
        if action == NotificationActions.SNOOZE:
            # Snooze for 1 minute
            self._snooze_time += 1 * 60  # 1 minute in seconds
            self._has_notified = False
            print(f"BGTaskService: Task snoozed for 1 minute. Total snooze: {self._snooze_time/60:.1f}m")
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action == NotificationActions.CANCEL:
            # Cancel the current task
            self._current_task = None
            self._snooze_time = 0
            self._has_notified = False
            print("BGTaskService: Task cancelled")
            self._running = False
            return Service.START_NOT_STICKY
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
        print(f"BGTaskService: Current Task expiry: {self._current_task.get('timestamp')}")

        while self._running and self._current_task is not None:
            if self._should_stop_service():
                print("BGTaskService: Stop flag detected, stopping service")
                break
            
            if self._is_task_expired() and not self._has_notified:
                print("BGTaskService: Task expired, showing notification")

                self.notification_manager.show_task_notification(
                    "Task Expired",
                    self._current_task.get("message")
                )
                self._has_notified = True
            
            time.sleep(WAIT_TIME)
    
    def _get_current_task(self):
        """
        Checks the first_task file and returns the Task if it is not expired.
        If the task is expired, it returns None.
        """
        try:
            path = self.service_task_file
            print(f"BGTaskService: Looking for first_task.json at: {path}")

            if not os.path.exists(path):
                return None

            with open(path, "r") as f:
                data = json.load(f)

            for date_key, tasks in data.items():
                if tasks:
                    task_time = datetime.fromisoformat(tasks[0].get("timestamp"))
                    if task_time > datetime.now():
                        return tasks[0]

            return None

        except Exception as e:
            print(f"BGTaskService: Error checking task file: {e}")
            return None
    
    def _is_task_expired(self):
        """Returns True if the current Task is expired"""
        try:
            timestamp_str = self._current_task.get("timestamp")
            task_time = datetime.fromisoformat(timestamp_str)

            trigger_time = task_time + timedelta(seconds=self._snooze_time)
            return datetime.now() >= trigger_time
        
        except Exception as e:
            print(f"BGTaskService: Error parsing timestamp: {e}")
            return False
    
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
    
    @staticmethod
    def _get_storage_path(path):
        """Returns the storage path"""
        app_dir = os.environ.get("ANDROID_PRIVATE", "")
        return os.path.join(app_dir, path)


class BGTaskNotificationManager:
    """Handles all notification related functionality"""
    
    def __init__(self):
        self.service = PythonService.mService
        self.context = self.service
        self.notification_manager = self.context.getSystemService(Context.NOTIFICATION_SERVICE)

        self._create_notification_channels()
    
    def _create_notification_channels(self):
        """Creates notification channels for Android 8.0+"""
        if BuildVersion.SDK_INT >= 26:
            # Foreground service channel
            service_channel = NotificationChannel(
                NotificationChannels.FOREGROUND_SERVICE,
                AndroidString("Task Service"),
                NotificationImportance.DEFAULT
            )
            service_channel.setDescription(AndroidString("Shows when the task monitor is active"))
            self.notification_manager.createNotificationChannel(service_channel)
            
            # Expired tasks channel
            expired_channel = NotificationChannel(
                NotificationChannels.EXPIRED_TASKS,
                AndroidString("Expired Task Alerts"),
                NotificationImportance.HIGH
            )
            expired_channel.setDescription(AndroidString("Alerts for expired tasks"))
            self.notification_manager.createNotificationChannel(expired_channel)
    
    def _create_pending_intent(self, action):
        """Creates a PendingIntent for the given action"""
        try:
            context = self.service.getApplicationContext()
            package_name = context.getPackageName()
            
            # Create intent based on action
            if action == NotificationActions.OPEN_APP:
                # Intent to open main activity
                intent = context.getPackageManager().getLaunchIntentForPackage(package_name)
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                request_code = NotificationActions.REQUEST_OPEN_APP
                
                # Create PendingIntent with proper flags
                flags = PendingIntent.FLAG_UPDATE_CURRENT
                if BuildVersion.SDK_INT >= 31:  # Android 12+
                    flags |= PendingIntent.FLAG_IMMUTABLE
                
                return PendingIntent.getActivity(context, request_code, intent, flags)
            else:
                # Create a broadcast intent with our custom action
                action_string = f"{package_name}.{action}"
                intent = Intent(AndroidString(action_string))
                intent.setPackage(package_name)  # Keep the broadcast within our app
                
                # Set request code based on action
                request_code = (NotificationActions.REQUEST_SNOOZE 
                              if action == NotificationActions.SNOOZE 
                              else NotificationActions.REQUEST_CANCEL)
                
                # Create PendingIntent with proper flags
                flags = PendingIntent.FLAG_UPDATE_CURRENT
                if BuildVersion.SDK_INT >= 31:  # Android 12+
                    flags |= PendingIntent.FLAG_IMMUTABLE
                
                print(f"BGTaskService: Creating broadcast PendingIntent for action {action_string}")
                return PendingIntent.getBroadcast(context, request_code, intent, flags)
            
        except Exception as e:
            print(f"BGTaskService: Error creating PendingIntent for {action}: {e}")
            return None

    def _build_notification(self, channel_id, title, text, priority):
        """Builds a notification with the given parameters"""
        builder = NotificationCompatBuilder(self.context, channel_id)
        builder.setContentTitle(AndroidString(title))
        builder.setContentText(AndroidString(text))
        builder.setSmallIcon(self.context.getApplicationInfo().icon)
        builder.setDefaults(NotificationCompat.DEFAULT_ALL)
        builder.setPriority(priority)
        
        # Add actions for expired task notifications
        if channel_id == NotificationChannels.EXPIRED_TASKS:
            print("BGTaskService: Building notification with action buttons")
            
            # Open app action (main action when clicking notification)
            open_app_intent = self._create_pending_intent(NotificationActions.OPEN_APP)
            if open_app_intent:
                builder.setContentIntent(open_app_intent)
                builder.setAutoCancel(True)  # Auto dismiss when clicked
            
            # Snooze action
            snooze_intent = self._create_pending_intent(NotificationActions.SNOOZE)
            if snooze_intent:
                # Use a standard icon for snooze (if available)
                snooze_icon = 0  # 0 means no icon
                if hasattr(NotificationCompat, "ic_pause_black_24dp"):
                    snooze_icon = NotificationCompat.ic_pause_black_24dp
                
                builder.addAction(snooze_icon, AndroidString("Snooze 1m"), snooze_intent)
                print("BGTaskService: Added snooze button")
            
            # Cancel action
            cancel_intent = self._create_pending_intent(NotificationActions.CANCEL)
            if cancel_intent:
                # Use a standard icon for cancel (if available)
                cancel_icon = 0  # 0 means no icon
                if hasattr(NotificationCompat, "ic_cancel_black_24dp"):
                    cancel_icon = NotificationCompat.ic_cancel_black_24dp
                
                builder.addAction(cancel_icon, AndroidString("Cancel"), cancel_intent)
                print("BGTaskService: Added cancel button")
        
        return builder.build()
    
    def show_foreground_notification(self, title, text):
        """Shows a foreground service notification"""
        try:
            notification = self._build_notification(
                NotificationChannels.FOREGROUND_SERVICE,
                title,
                text,
                NotificationPriority.LOW
            )
            self.service.startForeground(1, notification)
            print("BGTaskService: Foreground notification shown")
        except Exception as e:
            print(f"BGTaskService: Error showing foreground notification: {e}")
    
    def show_task_notification(self, title, message):
        """Shows a Task expired notification"""
        try:
            notification = self._build_notification(
                NotificationChannels.EXPIRED_TASKS,
                title or "Task Expired",
                message or "An expired Task needs your attention",
                NotificationPriority.HIGH
            )
            notification_id = int(time.time())
            self.notification_manager.notify(notification_id, notification)
            print("BGTaskService: Task notification sent successfully")
        except Exception as e:
            print(f"BGTaskService: Error showing task notification: {e}")


if __name__ == "__main__":
    print("BGTaskService: Starting background service")
    
    # Create and initialize service manager
    service_manager = BGTaskServiceManager()
    service_manager.remove_stop_flag()
    
    # Register broadcast receiver for our actions
    try:
        context = PythonService.mService.getApplicationContext()
        package_name = context.getPackageName()
        
        # Create broadcast receiver using Python-for-Android's API
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
            f"{package_name}.{NotificationActions.SNOOZE}",
            f"{package_name}.{NotificationActions.CANCEL}"
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
    if service_manager._current_task is not None:
        service_manager.init_notification_manager()
        # Show the startup notification
        service_manager.notification_manager.show_foreground_notification(
            "Task Monitor Active",
            f"Monitoring task due at {service_manager._current_task.get('timestamp')}"
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
            "No tasks to monitor"
        )
    
    print("BGTaskService: Service stopping")
