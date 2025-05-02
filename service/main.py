import json
import os
import time

from datetime import datetime, timedelta
from jnius import autoclass   # type: ignore

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
    
    def init_notification_manager(self):
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            self.notification_manager = BGTaskNotificationManager()
    
    def handle_action(self, action):
        """Handle notification actions"""
        if not self._current_task:
            return

        print(f"BGTaskService: Handling action: {action}")
        if action == NotificationActions.SNOOZE:
            # Snooze for 5 minutes
            self._snooze_time += 5 * 60  # 5 minutes in seconds
            print(f"BGTaskService: Task snoozed for 5 minutes. Total snooze: {self._snooze_time/60:.1f}m")
            # Stop the service and restart it to handle the snooze
            return Service.START_REDELIVER_INTENT
        
        elif action == NotificationActions.CANCEL:
            # Cancel the current task
            self._current_task = None
            self._snooze_time = 0
            print("BGTaskService: Task cancelled")
            self._running = False
            return Service.START_NOT_STICKY
        
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
            
            if self._is_task_expired():
                print("BGTaskService: Task expired, showing notification")

                self.notification_manager.show_task_notification(
                    "Task Expired",
                    self._current_task.get("message")
                )
            
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
    
    def _reset_task_state(self):
        """Reset the service state"""
        self._current_task = None
        self._snooze_time = None
    
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
            
            # Create intent based on action
            if action == NotificationActions.OPEN_APP:
                # Intent to open main activity
                package_name = context.getPackageName()
                intent = context.getPackageManager().getLaunchIntentForPackage(package_name)
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                request_code = NotificationActions.REQUEST_OPEN_APP
            else:
                # Intent for service actions (snooze/cancel)
                intent = Intent()
                intent.setClass(self.service, self.service.getClass())
                intent.setAction(AndroidString(action))
                
                # Set request code based on action
                request_code = (NotificationActions.REQUEST_SNOOZE 
                              if action == NotificationActions.SNOOZE 
                              else NotificationActions.REQUEST_CANCEL)
            
            # Create PendingIntent with proper flags
            flags = PendingIntent.FLAG_UPDATE_CURRENT
            if BuildVersion.SDK_INT >= 31:  # Android 12+
                flags |= PendingIntent.FLAG_IMMUTABLE
            
            # Use the application context for creating PendingIntents
            if action == NotificationActions.OPEN_APP:
                return PendingIntent.getActivity(context, request_code, intent, flags)
            else:
                return PendingIntent.getService(self.service, request_code, intent, flags)
            
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
            # Open app action (main action when clicking notification)
            open_app_intent = self._create_pending_intent(NotificationActions.OPEN_APP)
            if open_app_intent:
                builder.setContentIntent(open_app_intent)
                builder.setAutoCancel(True)  # Auto dismiss when clicked
            
            # Snooze action
            snooze_intent = self._create_pending_intent(NotificationActions.SNOOZE)
            if snooze_intent:
                builder.addAction(0, AndroidString("Snooze 5m"), snooze_intent)
            
            # Cancel action
            cancel_intent = self._create_pending_intent(NotificationActions.CANCEL)
            if cancel_intent:
                builder.addAction(0, AndroidString("Cancel"), cancel_intent)
        
        return builder.build()
    
    def show_foreground_notification(self, title, text):
        """Shows a foreground service notification"""
        try:
            notification = self._build_notification(
                NotificationChannels.FOREGROUND_SERVICE,
                title,
                text,
                NotificationPriority.DEFAULT
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
    
    service_manager = BGTaskServiceManager()
    service_manager.remove_stop_flag()
    
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
    else:
        # If no task, still show a notification but exit soon
        service_manager.init_notification_manager()
        service_manager.notification_manager.show_foreground_notification(
            "Task Monitor",
            "No tasks to monitor"
        )
    
    print("BGTaskService: Service stopping")
