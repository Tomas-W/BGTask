import json
import os
import time
from datetime import datetime

from jnius import autoclass, cast

# Constants
WAIT_TIME = 15  # seconds
SERVICE_FLAG_FILE = "app/src/assets/service_stop.flag"
SERVICE_TASK_FILE = "app/src/assets/first_task.json"

# Import required Java classes
PythonActivity = autoclass("org.kivy.android.PythonActivity")
PythonService = autoclass("org.kivy.android.PythonService")
NotificationManager = autoclass("android.app.NotificationManager")
NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationCompatBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
BuildVersion = autoclass("android.os.Build$VERSION")
Context = autoclass("android.content.Context")

def get_storage_path(path):
    """Returns the app-specific storage path for the given path."""
    app_dir = os.environ.get("ANDROID_PRIVATE", "")
    return os.path.join(app_dir, path)


def is_task_expired(task_data):
    if not task_data:
        return False

    timestamp_str = task_data.get("timestamp", "")
    if not timestamp_str:
        return False

    try:
        task_time = datetime.fromisoformat(timestamp_str)
        return datetime.now() >= task_time
    except Exception as e:
        print(f"BGTaskService: Error parsing timestamp: {e}")
        return False


def check_task_file():
    try:
        first_task_path = get_storage_path(SERVICE_TASK_FILE)
        print(f"BGTaskService: Looking for first_task.json at: {first_task_path}")

        if not os.path.exists(first_task_path):
            return False

        with open(first_task_path, "r") as f:
            data = json.load(f)

        for date_key, tasks in data.items():
            if tasks:
                task = tasks[0]
                if is_task_expired(task):
                    return task.get("message", "A task has expired")
        return False

    except Exception as e:
        print(f"BGTaskService: Error checking task file: {e}")
        return False


def should_stop_service():
    stop_flag_path = get_storage_path(SERVICE_FLAG_FILE)
    return os.path.exists(stop_flag_path)


def remove_stop_flag():
    stop_flag_path = get_storage_path(SERVICE_FLAG_FILE)
    if os.path.exists(stop_flag_path):
        try:
            os.remove(stop_flag_path)
        except Exception as e:
            print(f"BGTaskService: Error removing stop flag: {e}")


def show_foreground_notification(title, text):
    service = PythonService.mService
    context = service

    # Create notification channel for Android 8.0+
    channel_id = "task_channel"
    if BuildVersion.SDK_INT >= 26:
        channel = NotificationChannel(
            channel_id,
            "Task Service",
            NotificationManager.IMPORTANCE_DEFAULT
        )
        notification_manager = context.getSystemService(context.NOTIFICATION_SERVICE)
        notification_manager.createNotificationChannel(channel)

    # Build the notification
    builder = NotificationCompatBuilder(context, channel_id)
    builder.setContentTitle(title)
    builder.setContentText(text)
    builder.setSmallIcon(context.getApplicationInfo().icon)
    builder.setDefaults(NotificationCompat.DEFAULT_ALL)
    builder.setPriority(NotificationCompat.PRIORITY_DEFAULT)

    # Start foreground service
    service.startForeground(1, builder.build())


def show_notification(title, message):
    print("BGTaskService: Showing notification")
    try:
        service = PythonService.mService
        context = service
        
        # Get notification manager
        notification_manager = context.getSystemService(context.NOTIFICATION_SERVICE)

        # Create notification channel for Android 8.0+
        channel_id = "expired_task_channel"
        if BuildVersion.SDK_INT >= 26:
            channel = NotificationChannel(
                channel_id,
                "Expired Task Alerts",
                NotificationManager.IMPORTANCE_HIGH
            )
            notification_manager.createNotificationChannel(channel)

        # Build the notification
        builder = NotificationCompatBuilder(context, channel_id)
        builder.setContentTitle(title or "Task Expired")
        builder.setContentText(message or "An expired task needs your attention")
        builder.setSmallIcon(context.getApplicationInfo().icon)
        builder.setDefaults(NotificationCompat.DEFAULT_ALL)
        builder.setPriority(NotificationCompat.PRIORITY_HIGH)

        # Show the notification
        notification_id = int(time.time())
        notification_manager.notify(notification_id, builder.build())
        print("BGTaskService: Notification sent successfully")

    except Exception as e:
        print(f"BGTaskService: Error in show_notification: {e}")


if __name__ == "__main__":
    print("BGTaskService: Starting background service")

    remove_stop_flag()

    # Show the persistent foreground notification
    show_foreground_notification("Task Monitor Active", "Watching for expired tasks...")

    while True:
        if should_stop_service():
            print("BGTaskService: Stop flag detected, stopping service")
            break

        expired_message = check_task_file()
        if expired_message:
            print("BGTaskService: Found expired task")
            show_notification("Task Expired", expired_message)

        time.sleep(WAIT_TIME)
