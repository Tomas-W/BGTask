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
                "Task Service",
                NotificationImportance.DEFAULT
            )
            self.notification_manager.createNotificationChannel(service_channel)
            
            # Expired tasks channel
            expired_channel = NotificationChannel(
                NotificationChannels.EXPIRED_TASKS,
                "Expired Task Alerts",
                NotificationImportance.HIGH
            )
            self.notification_manager.createNotificationChannel(expired_channel)
    
    def _build_notification(self, channel_id, title, text, priority):
        """Builds a notification with the given parameters"""
        builder = NotificationCompatBuilder(self.context, channel_id)
        builder.setContentTitle(title)
        builder.setContentText(text)
        builder.setSmallIcon(self.context.getApplicationInfo().icon)
        builder.setDefaults(NotificationCompat.DEFAULT_ALL)
        builder.setPriority(priority)
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
    # Only run if there is a Task to monitor
    if service_manager._current_task is not None:
        
        service_manager.init_notification_manager()
    
        service_manager.remove_stop_flag()
        
        # service_manager._show_startup_notification()
        
        print("BGTaskService: Starting main service loop")
        # Main loop
        service_manager.run_service()
    
    print("BGTaskService: No Task to monitor, exiting")
