import time

from jnius import autoclass  # type: ignore

from service.service_logger import logger
from service.utils import ACTION, CHANNEL, IMPORTANCE, PRIORITY

AndroidString = autoclass("java.lang.String")
BuildVersion = autoclass('android.os.Build$VERSION')
Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
NotificationBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")  # Changed to androidx
NotificationChannel = autoclass("android.app.NotificationChannel")
PendingIntent = autoclass("android.app.PendingIntent")


class ServiceNotificationManager:
    def __init__(self, service):
        self.service = service
        self.context = service.getApplicationContext()
        self.notification_manager = self.context.getSystemService(Context.NOTIFICATION_SERVICE)
        
        self.package_name = self.context.getPackageName()
        self._init_foreground_channel()
        self._init_tasks_channel()
        
        # Track notification IDs
        self.active_notification_ids = set()
        self.current_notification_id = None
    
    def _init_foreground_channel(self):
        """Initialize the foreground channel"""
        try:
            foreground_channel = NotificationChannel(
                CHANNEL.FOREGROUND,
                AndroidString("BGTask Service"),
                IMPORTANCE.LOW
            )
            foreground_channel.setDescription(AndroidString("Shows when BGTask is monitoring your Tasks"))
            self.notification_manager.createNotificationChannel(foreground_channel)
            logger.debug("Created foreground channel")
        
        except Exception as e:
            logger.error(f"Error creating foreground channel: {e}")
    
    def _init_tasks_channel(self):
        """Initialize the tasks channel"""
        try:
            tasks_channel = NotificationChannel(
                CHANNEL.TASKS,
                AndroidString("BGTask Notifications"),
                IMPORTANCE.HIGH
            )
            tasks_channel.setDescription(AndroidString("Shows notifications for expired Tasks"))
            tasks_channel.enableVibration(True)
            tasks_channel.setShowBadge(True)
            self.notification_manager.createNotificationChannel(tasks_channel)
            logger.debug("Created tasks channel")
        
        except Exception as e:
            logger.error(f"Error creating tasks channel: {e}")
    
    def create_action_intent(self, action):
        """Create a broadcast intent for notification button actions"""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        
        # Set proper flags based on Android version
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if BuildVersion.SDK_INT >= 31:  # Android 12 or higher
            flags |= PendingIntent.FLAG_IMMUTABLE
        
        return PendingIntent.getBroadcast(
            self.context, 
            0,  # Request code
            intent,
            flags
        )
    
    def create_app_open_intent(self):
        """Create a PendingIntent to open the app's main activity"""
        try:
            # Get the launch intent for our package
            intent = self.context.getPackageManager().getLaunchIntentForPackage(self.package_name)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
            
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
    
    def _get_icon_resource(self):
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
    
    def show_foreground_notification(self, title, message, with_buttons=True):
        """Show a foreground notification with optional action buttons"""
        try:
            icon_id = self._get_icon_resource()
            if icon_id is None:
                logger.error("No valid icon found, cannot show notification")
                return
            
            # Create notification builder with proper channel
            builder = NotificationBuilder(self.context, CHANNEL.FOREGROUND)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            builder.setPriority(PRIORITY.LOW)
            builder.setOngoing(True)
            
            # Add click action to open app
            app_intent = self.create_app_open_intent()
            if app_intent:
                builder.setContentIntent(app_intent)
            
            if with_buttons:
                # Add Snooze button
                snooze_intent = self.create_action_intent(ACTION.SNOOZE_A)
                if snooze_intent:
                    builder.addAction(
                        0,  # No icon for buttons
                        AndroidString("Snooze 1m"),
                        snooze_intent
                    )
                
                # Add Cancel button
                cancel_intent = self.create_action_intent(ACTION.STOP)
                if cancel_intent:
                    builder.addAction(
                        0,  # No icon for buttons
                        AndroidString("Cancel"),
                        cancel_intent
                    )
            
            # Build and show notification
            notification = builder.build()
            self.service.startForeground(1, notification)
            logger.debug("Showed foreground notification")
            
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def show_task_notification(self, title, message):
        """Show a high-priority task notification with buttons"""
        try:
            icon_id = self._get_icon_resource()
            if icon_id is None:
                logger.error("No valid icon found, cannot show notification")
                return
            
            # Create notification builder with proper channel
            builder = NotificationBuilder(self.context, CHANNEL.TASKS)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            builder.setPriority(PRIORITY.HIGH)
            builder.setAutoCancel(True)  # Auto-cancel when clicked
            
            # Add click action to open app
            app_intent = self.create_app_open_intent()
            if app_intent:
                builder.setContentIntent(app_intent)
            
            # Add Snooze button
            snooze_intent = self.create_action_intent(ACTION.SNOOZE_A)
            if snooze_intent:
                builder.addAction(
                    0,
                    AndroidString("Snooze 1m"),
                    snooze_intent
                )
            
            # Add Cancel button
            cancel_intent = self.create_action_intent(ACTION.STOP)
            if cancel_intent:
                builder.addAction(
                    0,
                    AndroidString("Cancel"),
                    cancel_intent
                )
            
            # Show the notification with a unique ID
            self.current_notification_id = int(time.time())
            self.notification_manager.notify(self.current_notification_id, builder.build())
            # Add to active notifications set
            self.active_notification_ids.add(self.current_notification_id)
            logger.debug(f"Showed task notification with ID: {self.current_notification_id}")

            # from service.utils import AudioPlayer, PATH
            # audio_player = AudioPlayer()
            # audio_player.play(PATH.AUDIO_TASK_EXPIRED)
            
        except Exception as e:
            logger.error(f"Error showing task notification: {e}")
    
    def cancel_all_notifications(self):
        """Cancel all active notifications"""
        try:
            # Cancel each active notification
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
    
    def cancel_current_notification(self):
        """Cancel the current task notification if it exists"""
        if self.current_notification_id is not None:
            try:
                self.notification_manager.cancel(self.current_notification_id)
                self.active_notification_ids.discard(self.current_notification_id)
                self.current_notification_id = None
            
            except Exception as e:
                logger.error(f"Error cancelling notification: {e}")
    
    def remove_notification(self):
        """Remove the foreground notification"""
        try:
            self.service.stopForeground(True)
        
        except Exception as e:
            logger.error(f"Error removing notification: {e}")
