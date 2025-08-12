import time

from jnius import autoclass  # type: ignore
from typing import Any, TYPE_CHECKING

from managers.device.device_manager import DM

from src.utils.logger import logger

AndroidString = autoclass("java.lang.String")
BuildVersion = autoclass('android.os.Build$VERSION')
Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
NotificationBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
PendingIntent = autoclass("android.app.PendingIntent")
PowerManager = autoclass("android.os.PowerManager")

if TYPE_CHECKING:
    from service.service_expiry_manager import ServiceExpiryManager


class ServiceNotificationManager:

    WAKE_LOCK_STRING: str = "BGTask::TaskNotificationWakeLock"
    WAKE_LOCK_TIMEOUT: int = 1000

    ANDROID_12: int = 31

    GPS_TRACKING_NOTIFICATION_ID: int = 2000

    """Manages all Android notifications for the background service.
    - Foreground notification: Shows current Task status
    - Task notifications: High-priority alerts for expired Tasks
    
    It:
    - Creates and manages notification channels
    - Handles notification creation and updates
    - Manages notification actions (snooze, cancel)
    - Tracks active notifications for proper cleanup
    """
    def __init__(self, service: Any, expiry_manager: "ServiceExpiryManager"):
        self.service: Any = service
        self.context: Any = service.getApplicationContext()
        self.notification_manager: Any = self.context.getSystemService(Context.NOTIFICATION_SERVICE)
        self.expiry_manager: "ServiceExpiryManager" = expiry_manager
        
        self.package_name: str = self.context.getPackageName()
        self.task_notification_ids: set[int] = set()
        self.current_task_notification_id: int | None = None

        # GPS notification tracking
        self.current_gps_notification_id: int | None = None
        self.gps_tracking_notification_id: int = ServiceNotificationManager.GPS_TRACKING_NOTIFICATION_ID
        self.gps_notification_ids: set[int] = set()
        
        self._init_foreground_channel()
        self._init_tasks_channel()
        self._init_gps_channel()
    
    def _init_foreground_channel(self) -> None:
        """Initializes the foreground channel."""
        try:
            foreground_channel = NotificationChannel(
                DM.CHANNEL.FOREGROUND,
                AndroidString("BGTask Service"),
                DM.IMPORTANCE.LOW
            )
            foreground_channel.setDescription(AndroidString("Shows when BGTask is monitoring your Tasks"))
            self.notification_manager.createNotificationChannel(foreground_channel)
            logger.trace("Created foreground channel")
        
        except Exception as e:
            logger.error(f"Error creating foreground channel: {e}")
    
    def _init_tasks_channel(self) -> None:
        """Initializes the Tasks channel."""
        try:
            tasks_channel = NotificationChannel(
                DM.CHANNEL.TASKS,
                AndroidString("BGTask Notifications"),
                DM.IMPORTANCE.HIGH
            )
            tasks_channel.setDescription(AndroidString("Shows notifications for expired Tasks"))
            tasks_channel.enableVibration(True)
            tasks_channel.setShowBadge(True)
            self.notification_manager.createNotificationChannel(tasks_channel)
            logger.trace("Created Tasks channel")
        
        except Exception as e:
            logger.error(f"Error creating tasks channel: {e}")
    
    def _init_gps_channel(self) -> None:
        """Initializes the GPS notification channel."""
        try:
            gps_channel = NotificationChannel(
                DM.CHANNEL.GPS,
                AndroidString("BGTask Location"),
                DM.IMPORTANCE.LOW
            )
            gps_channel.setDescription(AndroidString("Shows location tracking and alerts"))
            self.notification_manager.createNotificationChannel(gps_channel)
            logger.trace("Created GPS channel")
        
        except Exception as e:
            logger.error(f"Error creating GPS channel: {e}")
    
    def create_action_intent(self, action: str, task_id: str) -> Any | None:
        """Creates a broadcast intent for notification button actions with task_id."""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        
        # Add task_id
        intent.putExtra("task_id", AndroidString(task_id))
        # Flags based on Android version
        flags = self._get_flags()
        # Request code based on action
        request_code = self._get_request_code(action, task_id)
        
        return PendingIntent.getBroadcast(
            self.context, 
            request_code,
            intent,
            flags
        )

    def _get_flags(self) -> int:
        """Returns the flags based on the action."""
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if BuildVersion.SDK_INT >= ServiceNotificationManager.ANDROID_12:
            flags |= PendingIntent.FLAG_IMMUTABLE
        return flags
    
    def _get_request_code(self, action: str, task_id: str) -> int:
        """Returns the request code based on the action and task ID."""
        base_code = 0
        # Tasks
        if action.endswith(DM.ACTION.SNOOZE_A):
            base_code = DM.INTENT.SNOOZE_A
        elif action.endswith(DM.ACTION.SNOOZE_B):
            base_code = DM.INTENT.SNOOZE_B
        elif action.endswith(DM.ACTION.CANCEL):
            base_code = DM.INTENT.CANCEL
        elif action.endswith(DM.ACTION.STOP_ALARM):
            base_code = DM.INTENT.STOP_ALARM
        
        # GPS
        elif action.endswith(DM.ACTION.CANCEL_GPS):
            base_code = DM.INTENT.CANCEL_GPS
        elif action.endswith(DM.ACTION.SKIP_GPS_TARGET):
            base_code = DM.INTENT.SKIP_GPS_TARGET
        
        # Add task_id hash to make unique
        id_hash = abs(hash(task_id[:4])) % 1000
        # Keep within Java int range
        return base_code + (id_hash * 10000)
    
    def create_app_open_intent(self, task_id: str | None = None) -> Any | None:
        """Creates a PendingIntent to open the App's main activity."""
        try:
            # Launch intent
            intent = self.context.getPackageManager().getLaunchIntentForPackage(self.package_name)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
            
            # Add task_id
            if task_id:
                intent.putExtra("task_id", AndroidString(task_id))
            
            # Flags based on Android version
            flags = self._get_flags()
            
            return PendingIntent.getActivity(
                self.context,
                DM.INTENT.OPEN_APP,
                intent,
                flags
            )
        except Exception as e:
            logger.error(f"Error creating app open intent: {e}")
            return None
    
    def show_foreground_notification(self, title: str, message: str, with_buttons: bool = True) -> None:
        """Shows a foreground notification with optional action buttons."""
        # Get icon resource
        icon_recource = self._get_icon_resource()
        if icon_recource is None:
            logger.error("No valid icon found, cannot show foreground notification")
            return
        
        # Create base notification
        builder = self._create_notification_builder(
            DM.CHANNEL.FOREGROUND,
            title,
            message,
            icon_recource,
            DM.PRIORITY.LOW
        )

        # Make builder foreground
        builder = self._make_builder_foreground(builder)
        if builder is None:
            return

        # Get current task for intent and buttons
        task = self.expiry_manager.current_task
        task_id = task.task_id if task else None

        # Add click to open app
        app_intent = self.create_app_open_intent(task_id=task_id)
        if app_intent:
            builder.setContentIntent(app_intent)

        # Add action buttons if requested
        if with_buttons and task_id:
            self._add_notification_buttons(builder, task_id)

        # Show notification
        try:
            notification = builder.build()
            self.service.startForeground(1, notification)
            task_log = DM.get_task_log(task) if task else "No tasks to monitor"
            logger.debug(f"Showed foreground notification for Task: {task_log}")
        
        except Exception as e:
            logger.error(f"Error showing foreground notification: {e}")
    
    def _create_notification_builder(self, channel: str, title: str, message: str, icon_id: int, priority: int) -> Any | None:
        """Creates a notification builder with basic settings."""
        try:
            builder = NotificationBuilder(self.context, channel)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            builder.setPriority(priority)
            return builder
        
        except Exception as e:
            logger.error(f"Error creating notification builder: {e}")
            return None
    
    def _make_builder_foreground(self, builder: Any) -> None:
        """
        Makes the builder a foreground notification by:
        - Making it persistent
        - Preventing auto-cancellation
        - Preventing re-alerting
        """
        if builder is None:
            return None
        
        try:
            builder.setOngoing(True)
            builder.setAutoCancel(False)
            builder.setOnlyAlertOnce(True)
            return builder
        
        except Exception as e:
            logger.error(f"Error making builder foreground: {e}")
            return None

    def _add_notification_buttons(self, builder: Any, task_id: str) -> None:
        """Adds action buttons to the notification."""
        actions = [
            (DM.ACTION.SNOOZE_A, "Snooze 1m"),
            (DM.ACTION.SNOOZE_B, "Snooze 1h"),
            (DM.ACTION.CANCEL, "Cancel")
        ]
        
        for action, label in actions:
            try:
                intent = self.create_action_intent(action, task_id)
                if intent:
                    builder.addAction(0, AndroidString(label), intent)
            except Exception as e:
                logger.error(f"Error adding {label} button: {e}")
    
    def _create_task_notification_builder(self, title: str, message: str, icon_id: int, task_id: str) -> Any | None:
        """Creates a notification builder with task-specific settings."""
        builder = self._create_notification_builder(
            DM.CHANNEL.TASKS,
            title,
            message,
            icon_id,
            DM.PRIORITY.MAX
        )
        if builder is None:
            return None

        try:
            # Set task-specific properties
            builder.setVisibility(NotificationCompat.VISIBILITY_PUBLIC)  # Show on lock screen
            builder.setAutoCancel(True)

            # Add full screen intent to wake up screen
            full_screen_intent = self.create_app_open_intent(task_id=task_id)
            if full_screen_intent:
                builder.setFullScreenIntent(full_screen_intent, True)

            # Add delete intent to cancel Task when notification is swiped
            delete_intent = self.create_action_intent(DM.ACTION.CANCEL, task_id)
            if delete_intent:
                builder.setDeleteIntent(delete_intent)

            # Click to open with direct intent
            app_intent = self.create_app_open_intent(task_id=task_id)
            if app_intent:
                builder.setContentIntent(app_intent)

            return builder
        except Exception as e:
            logger.error(f"Error setting up task notification: {e}")
            return None

    def _wake_up_screen(self) -> None:
        """Attempts to wake up the screen if it's locked."""
        try:
            power_manager = self.context.getSystemService(Context.POWER_SERVICE)
            wake_lock = power_manager.newWakeLock(
                PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP,
                ServiceNotificationManager.WAKE_LOCK_STRING
            )
            wake_lock.acquire(ServiceNotificationManager.WAKE_LOCK_TIMEOUT)
            wake_lock.release()
        except Exception as e:
            logger.error(f"Error waking up screen: {e}")

    def show_task_notification(self, title: str, message: str) -> None:
        """Shows a high-priority task notification with buttons."""
        # Get icon resource
        icon_resource = self._get_icon_resource()
        if icon_resource is None:
            logger.error("No valid icon found, cannot show notification")
            return

        if not self.expiry_manager.expired_task:
            logger.error("No expired task to show notification for")
            return

        task_id = self.expiry_manager.expired_task.task_id

        # Create and configure notification
        builder = self._create_task_notification_builder(title, message, icon_resource, task_id)
        if builder is None:
            return

        # Add action buttons
        self._add_notification_buttons(builder, task_id)

        # Show notification
        try:
            # Generate notification ID
            self.current_task_notification_id = int(time.time())
            notification = builder.build()
            
            # Show and track notification
            self.notification_manager.notify(self.current_task_notification_id, notification)
            self.task_notification_ids.add(self.current_task_notification_id)
            logger.debug(f"Showed Task notification for Task: {DM.get_task_log(self.expiry_manager.expired_task)}")

            # Attempt to wake up screen
            self._wake_up_screen()

        except Exception as e:
            logger.error(f"Error showing task notification: {e}")
    
    def cancel_task_notifications(self) -> None:
        """Cancels all active notifications."""
        if not self.task_notification_ids:
            return
        
        try:
            # Cancel all active notifications
            for notification_id in self.task_notification_ids:
                try:
                    self.notification_manager.cancel(notification_id)
                except Exception as e:
                    logger.error(f"Error cancelling notification {notification_id}: {e}")
            
            # Clear the active notifications set
            self.task_notification_ids.clear()
            self.current_task_notification_id = None
            logger.trace(f"Cancelled all notifications")
        
        except Exception as e:
            logger.error(f"Error cancelling all notifications: {e}")
    
    def remove_notification(self) -> None:
        """Removes the foreground notification."""
        try:
            self.service.stopForeground(True)
        
        except Exception as e:
            logger.error(f"Error removing notification: {e}")
    
    def _has_foreground_notification(self) -> bool:
        """Returns True if the foreground notification is active."""
        try:
            return len(self.notification_manager.getActiveNotifications()) > 0
        
        except Exception as e:
            logger.error(f"Error checking foreground status: {e}")
            return False
    
    def ensure_foreground_notification(self, title: str, message: str, with_buttons: bool = True) -> None:
        """Ensures the foreground notification is active, shows it if it's not."""
        logger.debug("Foreground notification not active, restoring it")
        self.show_foreground_notification(title, message, with_buttons)
    
    def _get_icon_resource(self) -> Any:
        """
        Returns the context to get the icon from.
        First tries to get the icon from the App's R.drawable.notification_icon.
        If that fails, it tries to get the icon from the App's ApplicationInfo.
        If that fails, it returns None.
        """
        icon_resource = self._get_task_icon()
        if icon_resource is None:
            icon_resource = self._get_default_icon()
        
        return icon_resource
    
    def _get_task_icon(self) -> int | None:
        """Returns the notification icon resource ID."""
        try:
            drawable = autoclass(f"{self.package_name}.R$drawable")
            return getattr(drawable, "notification_icon")
        
        except Exception as e:
            logger.error(f"Error getting custom notification icon: {e}")
            return None
    
    def _get_default_icon(self) -> int | None:
        """Returns the default notification icon resource ID."""
        try:
            return self.context.getApplicationInfo().icon
        except Exception as e:
            logger.error(f"Error getting default notification icon: {e}")
            return None

    def create_gps_action_intent(self, action: str, target_id: str = "current") -> Any | None:
        """Creates a broadcast intent for GPS notification actions."""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        
        # Add target_id for multi-target support
        intent.putExtra("target_id", AndroidString(target_id))
        
        flags = self._get_flags()
        request_code = self._get_request_code(action, target_id)
        
        return PendingIntent.getBroadcast(
            self.context, 
            request_code,
            intent,
            flags
        )

    def _add_gps_notification_buttons(self, builder: Any, target_id: str, has_next_target: bool = False) -> None:
        """Adds GPS-specific action buttons to notification."""
        actions = [
            (DM.ACTION.CANCEL_GPS, "Cancel Tracking")
        ]
        
        # Only add skip button if there are multiple targets
        if has_next_target:
            actions.append((DM.ACTION.SKIP_GPS_TARGET, "Skip to Next"))
        
        for action, label in actions:
            try:
                intent = self.create_gps_action_intent(action, target_id)
                if intent:
                    builder.addAction(0, AndroidString(label), intent)
            except Exception as e:
                logger.error(f"Error adding GPS {label} button: {e}")

    def show_gps_tracking_notification(self, distance: float, target_name: str = "target", 
                                     target_id: str = "current", has_next_target: bool = False) -> None:
        """Shows/updates the ongoing GPS tracking notification."""
        icon_resource = self._get_icon_resource()
        if icon_resource is None:
            logger.error("No valid icon found, cannot show GPS tracking notification")
            return

        # Format distance
        if distance == -1:
            distance_str = "calculating..."
        elif distance >= 1000:
            distance_str = f"{distance / 1000:.1f} km"
        else:
            distance_str = f"{distance:.0f} m"

        # Create notification
        builder = self._create_notification_builder(
            DM.CHANNEL.GPS,
            f"Tracking: {target_name}",
            f"Distance: {distance_str}",
            icon_resource,
            DM.PRIORITY.LOW
        )
        
        if builder is None:
            return

        try:
            # Make it ongoing but not foreground
            builder.setOngoing(True)
            builder.setAutoCancel(False)
            builder.setOnlyAlertOnce(True)  # Don't alert on updates

            # Add click to open app
            app_intent = self.create_app_open_intent()
            if app_intent:
                builder.setContentIntent(app_intent)

            # Add GPS buttons
            self._add_gps_notification_buttons(builder, target_id, has_next_target)

            notification = builder.build()
            self.notification_manager.notify(self.gps_tracking_notification_id, notification)
            self.gps_notification_ids.add(self.gps_tracking_notification_id)
            
            logger.debug(f"Updated GPS tracking notification: {distance_str} to {target_name}")

        except Exception as e:
            logger.error(f"Error showing GPS tracking notification: {e}")

    def show_gps_alert_notification(self, target_name: str = "target", target_id: str = "current", 
                                   has_next_target: bool = False) -> None:
        """Shows a high-priority GPS alert notification when target is reached."""
        icon_resource = self._get_icon_resource()
        if icon_resource is None:
            logger.error("No valid icon found, cannot show GPS alert notification")
            return

        builder = self._create_notification_builder(
            DM.CHANNEL.GPS,
            "Reached distance target!",
            f"You are near: {target_name}",
            icon_resource,
            DM.PRIORITY.HIGH
        )
        
        if builder is None:
            return

        try:
            # Make it alerting
            builder.setAutoCancel(True)
            builder.setOnlyAlertOnce(False)

            # Add vibration and sound
            builder.setDefaults(NotificationCompat.DEFAULT_ALL)

            # Add click to open app
            app_intent = self.create_app_open_intent()
            if app_intent:
                builder.setContentIntent(app_intent)

            # Add GPS buttons
            self._add_gps_notification_buttons(builder, target_id, has_next_target)

            # Generate unique ID for alert
            self.current_gps_notification_id = int(time.time())
            notification = builder.build()
            
            self.notification_manager.notify(self.current_gps_notification_id, notification)
            self.gps_notification_ids.add(self.current_gps_notification_id)
            logger.info(f"Showed GPS alert notification for {target_name}")

            # Wake up screen for important alert
            self._wake_up_screen()

        except Exception as e:
            logger.error(f"Error showing GPS alert notification: {e}")

    def cancel_gps_notifications(self) -> None:
        """Cancels all GPS-related notifications."""
        for notification_id in self.gps_notification_ids:
            try:
                self.notification_manager.cancel(notification_id)
            except Exception as e:
                logger.error(f"Error cancelling tracked notification {notification_id}: {e}")
        
        self.gps_notification_ids.clear()
        self.current_gps_notification_id = None
        logger.debug("Cancelled all GPS notifications")