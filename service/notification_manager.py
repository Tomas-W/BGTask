from jnius import autoclass, cast

# Android classes
Context = autoclass("android.content.Context")
PendingIntent = autoclass("android.app.PendingIntent")
Intent = autoclass("android.content.Intent")
NotificationBuilder = autoclass("android.app.Notification$Builder")
NotificationManager = autoclass("android.app.NotificationManager")
AndroidString = autoclass("java.lang.String")

class NotificationManager:
    def __init__(self, service):
        self.service = service
        self.context = service.getApplicationContext()
        self.notification_manager = self.context.getSystemService(Context.NOTIFICATION_SERVICE)
        self.package_name = self.context.getPackageName()
        
    def create_action_intent(self, action):
        """Create a broadcast intent for notification button actions"""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        # Use FLAG_UPDATE_CURRENT to ensure we get a unique pending intent
        return PendingIntent.getBroadcast(
            self.context, 
            0,  # Request code
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT
        )
    
    def show_foreground_notification(self, title, message, with_buttons=True):
        """Show a foreground notification with optional action buttons"""
        try:
            # Create notification builder
            builder = NotificationBuilder(self.context)
            builder.setContentTitle(AndroidString(title.encode("utf-8")))
            builder.setContentText(AndroidString(message.encode("utf-8")))
            builder.setOngoing(True)  # Make it persistent
            
            # Set small icon (required)
            Drawable = autoclass(f"{self.package_name}.R$drawable")
            icon = getattr(Drawable, "icon")
            builder.setSmallIcon(icon)
            
            if with_buttons:
                # Add Snooze button
                snooze_intent = self.create_action_intent("SNOOZE")
                builder.addAction(
                    icon,  # Icon for button
                    AndroidString("Snooze".encode("utf-8")),
                    snooze_intent
                )
                
                # Add Cancel button
                cancel_intent = self.create_action_intent("CANCEL")
                builder.addAction(
                    icon,  # Icon for button
                    AndroidString("Cancel".encode("utf-8")),
                    cancel_intent
                )
            
            # Build and show notification
            notification = builder.build()
            self.service.startForeground(1, notification)
            print("NotificationManager: Showed foreground notification")
            
        except Exception as e:
            print(f"NotificationManager: Error showing notification: {e}")
    
    def remove_notification(self):
        """Remove the foreground notification"""
        try:
            self.service.stopForeground(True)
            print("NotificationManager: Removed foreground notification")
        except Exception as e:
            print(f"NotificationManager: Error removing notification: {e}") 