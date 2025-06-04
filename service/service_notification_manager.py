import time

from jnius import autoclass  # type: ignore
from typing import Any, TYPE_CHECKING

from service.service_device_manager import DM

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
    """Manages all Android notifications for the background service.
    - Foreground notification: Keeps the service alive and shows current Task status
    - Task notifications: High-priority alerts for expired Tasks
    
    It:
    - Creates and manages notification channels
    - Handles notification creation and updates
    - Manages notification actions (snooze, cancel)
    - Tracks active notifications for proper cleanup
    """
    def __init__(self, service: Any, expiry_manager: "ServiceExpiryManager"	):
        self.service: Any = service
        self.context: Any = service.getApplicationContext()
        self.notification_manager: Any = self.context.getSystemService(Context.NOTIFICATION_SERVICE)
        self.expiry_manager: "ServiceExpiryManager" = expiry_manager
        
        self.package_name: str = self.context.getPackageName()
        self.active_notification_ids: set[int] = set()
        self.current_notification_id: int | None = None
        
        self._init_foreground_channel()
        self._init_tasks_channel()
    
    def _init_foreground_channel(self) -> None:
        """Initialize the foreground channel"""
        try:
            foreground_channel = NotificationChannel(
                DM.CHANNEL.FOREGROUND,
                AndroidString("BGTask Service"),
                DM.IMPORTANCE.LOW
            )
            foreground_channel.setDescription(AndroidString("Shows when BGTask is monitoring your Tasks"))
            self.notification_manager.createNotificationChannel(foreground_channel)
            logger.debug("Created foreground channel")
        
        except Exception as e:
            logger.error(f"Error creating foreground channel: {e}")
    
    def _init_tasks_channel(self) -> None:
        """Initialize the tasks channel"""
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
            logger.debug("Created tasks channel")
        
        except Exception as e:
            logger.error(f"Error creating tasks channel: {e}")
    
    def create_action_intent(self, action: str, task_id: str) -> Any | None:
        """Create a broadcast intent for notification button actions with task_id"""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        
        # Add task_id to the intent
        intent.putExtra("task_id", AndroidString(task_id))
        logger.debug(f"Adding task_id: {task_id} to intent")
        
        # Set flags based on Android version
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if BuildVersion.SDK_INT >= 31:  # Android 12 or higher
            flags |= PendingIntent.FLAG_IMMUTABLE
        
        # Use different request codes for different actions
        request_code = 0
        if action.endswith(DM.ACTION.SNOOZE_A):
            request_code = DM.INTENT.SNOOZE_A
        elif action.endswith(DM.ACTION.SNOOZE_B):
            request_code = DM.INTENT.SNOOZE_B
        elif action.endswith(DM.ACTION.CANCEL):
            request_code = DM.INTENT.CANCEL
        elif action.endswith(DM.ACTION.OPEN_APP):
            request_code = DM.INTENT.OPEN_APP
        
        logger.debug(f"Creating PendingIntent with request_code: {request_code}")
        return PendingIntent.getBroadcast(
            self.context, 
            request_code,
            intent,
            flags
        )
    
    def create_app_open_intent(self, task_id: str | None = None) -> Any | None:
        """Create a PendingIntent to open the app's main activity"""
        try:
            # Get the launch intent
            intent = self.context.getPackageManager().getLaunchIntentForPackage(self.package_name)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
            
            # Add task_id if provided
            if task_id:
                intent.putExtra("task_id", AndroidString(task_id))
            
            # Set proper flags based on Android version
            flags = PendingIntent.FLAG_UPDATE_CURRENT
            if BuildVersion.SDK_INT >= 31:  # Android 12 or higher
                flags |= PendingIntent.FLAG_IMMUTABLE
            
            return PendingIntent.getActivity(
                self.context,
                0,  # Request code
                intent,
                flags
            )
        except Exception as e:
            logger.error(f"Error creating app open intent: {e}")
            return None
    
    def _get_icon_resource(self) -> int | None:
        """Get the notification icon resource ID"""
        try:
            drawable = autoclass(f"{self.package_name}.R$drawable")
            return getattr(drawable, "notification_icon")

        except Exception as e:
            logger.error(f"Error getting notification icon: {e}")
            try:
                # Fallback to app icon
                return self.context.getApplicationInfo().icon

            except Exception as e:
                logger.error(f"Error getting app icon: {e}")
                return None
    
    def show_foreground_notification(self, title: str, message: str, with_buttons: bool = True) -> None:
        """Show a foreground notification with optional action buttons"""
        try:
            icon_id = self._get_icon_resource()
            if icon_id is None:
                logger.error("No valid icon found, cannot show notification")
                return
            
            try:
                # Create notification builder
                builder = NotificationBuilder(self.context, DM.CHANNEL.FOREGROUND)
                builder.setContentTitle(AndroidString(title))
                builder.setContentText(AndroidString(message))
                builder.setSmallIcon(icon_id)
                builder.setPriority(DM.PRIORITY.LOW)
                builder.setOngoing(True)        # Make persistent
                builder.setAutoCancel(False)    # Prevent auto-cancellation
                builder.setOnlyAlertOnce(True)  # Prevent re-alerting
            
            except Exception as e:
                logger.error(f"Error creating notification builder: {e}")
            
            try:
                # Add click action to open app (without canceling task)
                # Use expired task if available, otherwise use current task
                task = self.expiry_manager.expired_task or self.expiry_manager.current_task
                task_id = task.task_id if task else None
                app_intent = self.create_app_open_intent(task_id=task_id)
                if app_intent:
                    builder.setContentIntent(app_intent)
            
            except Exception as e:
                logger.error(f"Error creating app open intent: {e}")
            
            if with_buttons:
                # Use expired task if available, otherwise use current task
                task = self.expiry_manager.expired_task or self.expiry_manager.current_task
                if task:
                    task_id = task.task_id
                    try:
                        # Add Snooze A button
                        snooze_intent = self.create_action_intent(DM.ACTION.SNOOZE_A, task_id)
                        if snooze_intent:
                            builder.addAction(
                                0,  # No icon for buttons
                                AndroidString("Snooze 1m"),
                                snooze_intent
                            )
                    
                    except Exception as e:
                        logger.error(f"Error adding snooze button: {e}")
                    
                    try:
                        # Add Snooze B button
                        snooze_intent = self.create_action_intent(DM.ACTION.SNOOZE_B, task_id)
                        if snooze_intent:
                            builder.addAction(
                                0,  # No icon for buttons
                                AndroidString("Snooze 1h"),
                                snooze_intent
                            )
                    
                    except Exception as e:
                        logger.error(f"Error adding snooze button: {e}")
                    
                    try:
                        # Add Cancel button
                        cancel_intent = self.create_action_intent(DM.ACTION.CANCEL, task_id)
                        if cancel_intent:
                            builder.addAction(
                                0,  # No icon for buttons
                                AndroidString("Cancel"),
                                cancel_intent
                            )
                    
                    except Exception as e:
                        logger.error(f"Error adding cancel button: {e}")
            
            
            try:
                # Build and show notification
                notification = builder.build()
                self.service.startForeground(1, notification)
                logger.debug("Showed foreground notification")
            
            except Exception as e:
                logger.error(f"Error showing foreground notification: {e}")
        
        except Exception as e:
            logger.error(f"Error in show_foreground_notification: {e}")
    
    def show_task_notification(self, title: str, message: str) -> None:
        """Show a high-priority task notification with buttons"""
        try:
            icon_id = self._get_icon_resource()
            if icon_id is None:
                logger.error("No valid icon found, cannot show notification")
                return
            
            if not self.expiry_manager.expired_task:
                logger.error("No expired task to show notification for")
                return
            
            task_id = self.expiry_manager.expired_task.task_id
            
            # Create notification builder
            builder = NotificationBuilder(self.context, DM.CHANNEL.TASKS)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            
            # Set maximum priority and visibility
            builder.setPriority(DM.PRIORITY.MAX)
            builder.setVisibility(NotificationCompat.VISIBILITY_PUBLIC)  # Show on lock screen
            builder.setAutoCancel(True)
            
            # Add full screen intent to wake up screen
            full_screen_intent = self.create_app_open_intent(task_id=task_id)
            if full_screen_intent:
                builder.setFullScreenIntent(full_screen_intent, True)
            
            # Add delete intent to cancel task when notification is swiped
            delete_intent = self.create_action_intent(DM.ACTION.CANCEL, task_id)
            if delete_intent:
                builder.setDeleteIntent(delete_intent)
            
            # Add click action to open app via broadcast
            app_intent = self.create_action_intent(DM.ACTION.OPEN_APP, task_id)
            if app_intent:
                builder.setContentIntent(app_intent)
            
            # Add Snooze A button
            snooze_intent = self.create_action_intent(DM.ACTION.SNOOZE_A, task_id)
            if snooze_intent:
                builder.addAction(
                    0,  # No icon for buttons
                    AndroidString("Snooze 1m"),
                    snooze_intent
                )
            
            # Add Snooze B button
            snooze_intent = self.create_action_intent(DM.ACTION.SNOOZE_B, task_id)
            if snooze_intent:
                builder.addAction(
                    0,  # No icon for buttons
                    AndroidString("Snooze 1h"),
                    snooze_intent
                )
            
            # Add Cancel button
            cancel_intent = self.create_action_intent(DM.ACTION.CANCEL, task_id)
            if cancel_intent:
                builder.addAction(
                    0,  # No icon for buttons
                    AndroidString("Cancel"),
                    cancel_intent
                )
            
            # Show notification with a unique ID
            self.current_notification_id = int(time.time())
            self.notification_manager.notify(self.current_notification_id, builder.build())
            # Add to active notifications set
            self.active_notification_ids.add(self.current_notification_id)
            logger.debug(f"Showed task notification with ID: {self.current_notification_id}")
            
            # Wake up screen if locked
            try:
                power_manager = self.context.getSystemService(Context.POWER_SERVICE)
                wake_lock = power_manager.newWakeLock(
                    PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP,
                    "BGTask::TaskNotificationWakeLock"
                )
                wake_lock.acquire(1000)  # Wake for 1 second
                wake_lock.release()
            except Exception as e:
                logger.error(f"Error waking up screen: {e}")
        
        except Exception as e:
            logger.error(f"Error showing task notification: {e}")
    
    def cancel_all_notifications(self) -> None:
        """Cancel all active notifications"""
        if not self.active_notification_ids:
            return
        
        try:
            # Cancel all active notifications
            for notification_id in self.active_notification_ids:
                try:
                    self.notification_manager.cancel(notification_id)
                except Exception as e:
                    logger.error(f"Error cancelling notification {notification_id}: {e}")
            
            # Clear the active notifications set
            self.active_notification_ids.clear()
            self.current_notification_id = None
        
        except Exception as e:
            logger.error(f"Error cancelling all notifications: {e}")
    
    def cancel_current_notification(self) -> None:
        """Cancel the current Task notification if it exists"""
        if self.current_notification_id is not None:
            try:
                self.notification_manager.cancel(self.current_notification_id)
                self.active_notification_ids.discard(self.current_notification_id)
                self.current_notification_id = None
            
            except Exception as e:
                logger.error(f"Error cancelling notification: {e}")
    
    def remove_notification(self) -> None:
        """Remove the foreground notification"""
        try:
            self.service.stopForeground(True)
        
        except Exception as e:
            logger.error(f"Error removing notification: {e}")
    
    def _has_foreground_notification(self) -> bool:
        """Check if the foreground notification is active"""
        try:
            return len(self.notification_manager.getActiveNotifications()) > 0
        
        except Exception as e:
            logger.error(f"Error checking foreground status: {e}")
            return False
    
    def ensure_foreground_notification(self, title: str, message: str, with_buttons: bool = True) -> None:
        """Ensure the foreground notification is active, show it if it's not"""
        logger.debug("Foreground notification not active, restoring it")
        self.show_foreground_notification(title, message, with_buttons)
