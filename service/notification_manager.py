import time

from jnius import autoclass, cast  # type: ignore
from service.utils import ACTION, CHANNEL, PRIORITY, IMPORTANCE
# Android classes
Context = autoclass("android.content.Context")
PendingIntent = autoclass("android.app.PendingIntent")
Intent = autoclass("android.content.Intent")
NotificationBuilder = autoclass("androidx.core.app.NotificationCompat$Builder")  # Changed to androidx
NotificationManagerCompat = autoclass("androidx.core.app.NotificationManagerCompat")
NotificationChannel = autoclass("android.app.NotificationChannel")
AndroidString = autoclass("java.lang.String")
BuildVersion = autoclass('android.os.Build$VERSION')

class NotificationManager:
    def __init__(self, service):
        self.service = service
        self.context = service.getApplicationContext()
        try:
            # Try androidx NotificationManagerCompat
            self.notification_manager = NotificationManagerCompat.From(self.context)
        except Exception as e:
            print(f"NotificationManager: Error using NotificationManagerCompat: {e}")
            # Fallback to standard NotificationManager
            self.notification_manager = self.context.getSystemService(Context.NOTIFICATION_SERVICE)
        
        self.package_name = self.context.getPackageName()
        self._create_notification_channels()
        # Track all active notification IDs
        self.active_notification_ids = set()
        self.current_notification_id = None
    
    def _create_notification_channels(self):
        """Create notification channels for Android 8.0+"""
        if BuildVersion.SDK_INT >= 26:
            # Foreground service channel
            foreground_channel = NotificationChannel(
                CHANNEL.FOREGROUND,
                AndroidString("Task Service"),
                IMPORTANCE.LOW
            )
            foreground_channel.setDescription(AndroidString("Shows when the task monitor is active"))
            
            # Tasks channel (for expired tasks)
            tasks_channel = NotificationChannel(
                CHANNEL.TASKS,
                AndroidString("Task Notifications"),
                IMPORTANCE.HIGH
            )
            tasks_channel.setDescription(AndroidString("Shows notifications for expired tasks"))
            tasks_channel.enableVibration(True)
            tasks_channel.setShowBadge(True)
            
            # Register the channels
            self.notification_manager.createNotificationChannel(foreground_channel)
            self.notification_manager.createNotificationChannel(tasks_channel)
            print("NotificationManager: Created notification channels")
        
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
    
    def _get_icon_resource(self):
        """Get the notification icon resource ID"""
        try:
            drawable = autoclass(f"{self.package_name}.R$drawable")
            return getattr(drawable, "notification_icon")
        except Exception as e:
            print(f"NotificationManager: Error getting notification icon: {e}")
            try:
                # Fallback to app icon
                return self.context.getApplicationInfo().icon
            except Exception as e:
                print(f"NotificationManager: Error getting app icon: {e}")
                return None
    
    def show_foreground_notification(self, title, message, with_buttons=True):
        """Show a foreground notification with optional action buttons"""
        try:
            # Get icon first
            icon_id = self._get_icon_resource()
            if icon_id is None:
                print("NotificationManager: No valid icon found, cannot show notification")
                return
            
            # Create notification builder with proper channel
            builder = NotificationBuilder(self.context, CHANNEL.FOREGROUND)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            builder.setPriority(PRIORITY.LOW)
            builder.setOngoing(True)
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
            print("NotificationManager: Showed foreground notification")
            
        except Exception as e:
            print(f"NotificationManager: Error showing notification: {e}")
    
    def show_task_notification(self, title, message):
        """Show a high-priority task notification with buttons"""
        try:
            # Get icon first
            icon_id = self._get_icon_resource()
            if icon_id is None:
                print("NotificationManager: No valid icon found, cannot show notification")
                return
            
            # Create notification builder with proper channel
            builder = NotificationBuilder(self.context, CHANNEL.TASKS)
            builder.setContentTitle(AndroidString(title))
            builder.setContentText(AndroidString(message))
            builder.setSmallIcon(icon_id)
            builder.setPriority(PRIORITY.HIGH)
            builder.setAutoCancel(True)  # Auto-cancel when clicked
            
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
            print(f"NotificationManager: Showed task notification with ID: {self.current_notification_id}")
            
        except Exception as e:
            print(f"NotificationManager: Error showing task notification: {e}")
    
    def cancel_all_notifications(self):
        """Cancel all active notifications"""
        try:
            # Cancel each active notification
            for notification_id in self.active_notification_ids:
                try:
                    self.notification_manager.cancel(notification_id)
                    print(f"NotificationManager: Cancelled notification {notification_id}")
                except Exception as e:
                    print(f"NotificationManager: Error cancelling notification {notification_id}: {e}")
            
            # Clear the active notifications set
            self.active_notification_ids.clear()
            self.current_notification_id = None
            print("NotificationManager: All notifications cancelled")
        except Exception as e:
            print(f"NotificationManager: Error in cancel_all_notifications: {e}")
    
    def cancel_current_notification(self):
        """Cancel the current task notification if it exists"""
        if self.current_notification_id is not None:
            try:
                self.notification_manager.cancel(self.current_notification_id)
                print(f"NotificationManager: Cancelled notification {self.current_notification_id}")
                # Remove from active notifications set
                self.active_notification_ids.discard(self.current_notification_id)
                self.current_notification_id = None
            except Exception as e:
                print(f"NotificationManager: Error cancelling notification: {e}")
    
    def remove_notification(self):
        """Remove the foreground notification"""
        try:
            self.service.stopForeground(True)
            print("NotificationManager: Removed foreground notification")
        except Exception as e:
            print(f"NotificationManager: Error removing notification: {e}") 