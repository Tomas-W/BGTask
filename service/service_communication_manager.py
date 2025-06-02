from typing import TYPE_CHECKING, Any

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore

from service.service_device_manager import DM
from src.utils.logger import logger

AndroidString = autoclass("java.lang.String")
Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")

if TYPE_CHECKING:
    from service.service_manager import ServiceManager
    from service.service_audio_manager import ServiceAudioManager
    from service.service_expiry_manager import ServiceExpiryManager
    from service.service_notification_manager import ServiceNotificationManager


class ServiceCommunicationManager:
    """
    Manages all communication within the Service and with the App.
    Handles actions from notifications, broadcasts, and app communication.
    """
    def __init__(self,
                 service_manager: "ServiceManager",
                 audio_manager: "ServiceAudioManager",
                 expiry_manager: "ServiceExpiryManager",
                 notification_manager: "ServiceNotificationManager"):
        
        self.service_manager: "ServiceManager" = service_manager
        self.audio_manager: "ServiceAudioManager" = audio_manager
        self.expiry_manager: "ServiceExpiryManager" = expiry_manager
        self.notification_manager: "ServiceNotificationManager" = notification_manager

        self.context: Any | None = None
        self.package_name: str | None = None
        self.receiver: BroadcastReceiver | None = None

        self._init_context()
        self._init_receiver()

    def _init_context(self) -> None:
        """Initialize the service context"""
        try:
            if hasattr(PythonService, "mService") and PythonService.mService:
                self.context = PythonService.mService.getApplicationContext()
                self.package_name = self.context.getPackageName()
                logger.debug("Initialized service communication manager")
            else:
                logger.error("Could not initialize context - service context not available")
        
        except Exception as e:
            logger.error(f"Error initializing service context: {e}")

    def _init_receiver(self) -> None:
        """Initialize broadcast receiver for receiving all actions"""
        try:
            if not self.context:
                logger.error("Cannot initialize receiver - no context available")
                return

            # Define all actions to listen for
            actions = [
                # Internal actions
                f"{self.package_name}.{DM.ACTION.SNOOZE_A}",
                f"{self.package_name}.{DM.ACTION.SNOOZE_B}",
                f"{self.package_name}.{DM.ACTION.CANCEL}",
                f"{self.package_name}.{DM.ACTION.OPEN_APP}",
                f"{self.package_name}.{DM.ACTION.RESTART_SERVICE}",
                # App communication actions
                f"{self.package_name}.{DM.ACTION.STOP_ALARM}",
                f"{self.package_name}.{DM.ACTION.UPDATE_TASKS}",
                f"{self.package_name}.{DM.ACTION.REMOVE_TASK_NOTIFICATIONS}",
                # Boot action
                f"{DM.ACTION.BOOT_ACTION}.{DM.ACTION.BOOT_COMPLETED}"
            ]

            # Create and start the receiver
            self.receiver = BroadcastReceiver(
                self._receiver_callback,
                actions=actions
            )
            self.receiver.start()
            logger.debug(f"Started broadcast receiver for actions: {actions}")
            
        except Exception as e:
            logger.error(f"Error initializing broadcast receiver: {e}")

    def _receiver_callback(self, context: Any, intent: Any) -> None:
        """Handles all actions received through the broadcast receiver"""
        try:
            # No need for target check
            # Must listen for all actions
            
            action = intent.getAction()
            if not action:
                logger.error("Received intent with null action")
                return
                
            pure_action = action.split(".")[-1]
            logger.debug(f"ServiceCommunicationManager received action: {pure_action}")
            
            # Handle boot action
            if pure_action == DM.ACTION.BOOT_COMPLETED:
                from service.main import start_service
                start_service()
                return

            # Handle app communication actions
            if pure_action == DM.ACTION.UPDATE_TASKS:
                self._update_tasks_action()
                return
            elif pure_action == DM.ACTION.STOP_ALARM:
                self._stop_alarm_action()
                return
            elif pure_action == DM.ACTION.OPEN_APP:
                self.service_manager._open_app()
                return
            elif pure_action == DM.ACTION.REMOVE_TASK_NOTIFICATIONS:
                self.notification_manager.cancel_all_notifications()
                return


            # Handle notification actions
            self.handle_action(pure_action, intent)
                
        except Exception as e:
            logger.error(f"Error in broadcast receiver callback: {e}")

    def handle_action(self, action: str, intent: Any) -> int:
        """Handles notification button actions from foreground or Task notifications."""
        logger.debug(f"ServiceCommunicationManager.handle_action received: {action}")
        
        # Log all extras from intent
        if intent:
            bundle = intent.getExtras()
            if bundle:
                logger.debug("Intent extras:")
                for key in bundle.keySet():
                    value = bundle.get(key)
                    logger.debug(f"  {key}: {value}")
        
        notification_type = intent.getStringExtra("notification_type")
        logger.debug(f"Action from notification type: {notification_type}")
        
        # Cancel all notifications
        self.notification_manager.cancel_all_notifications()
        
        # Only handle notification button actions
        if not any(action.endswith(btn_action) for btn_action in [
            DM.ACTION.SNOOZE_A,
            DM.ACTION.SNOOZE_B,
            DM.ACTION.CANCEL,
            DM.ACTION.OPEN_APP,
        ]):
            return Service.START_STICKY
        
        # Get task data based on notification type
        task_data = None
        if notification_type == DM.NOTIFICATION_TYPE.FOREGROUND and self.expiry_manager.current_task:
            logger.error(f"FOREGROUND NOTIFICATION RECEIVED: {self.expiry_manager.current_task.message}")
            task_data = {
                "task_id": self.expiry_manager.current_task.task_id,
                "notification_type": notification_type
            }
        elif notification_type == DM.NOTIFICATION_TYPE.EXPIRED and self.expiry_manager.expired_task:
            logger.error(f"EXPIRED NOTIFICATION RECEIVED: {self.expiry_manager.expired_task.message}")
            task_data = {
                "task_id": self.expiry_manager.expired_task.task_id,
                "notification_type": notification_type
            }
        else:
            logger.error(f"UNKNOWN NOTIFICATION TYPE RECEIVED: {notification_type}")
        
        # Handle the actions
        if action.endswith(DM.ACTION.SNOOZE_A) or action.endswith(DM.ACTION.SNOOZE_B):
            self.expiry_manager.snooze_task(action)
            self.audio_manager.stop_alarm()
            self.service_manager.update_foreground_notification_info()
            self.send_action(DM.ACTION.UPDATE_TASKS, task_data)
            self.send_action(DM.ACTION.STOP_ALARM)
            return Service.START_STICKY
        
        elif action.endswith(DM.ACTION.CANCEL) or action.endswith(DM.ACTION.OPEN_APP):
            self.expiry_manager.cancel_task()
            self.audio_manager.stop_alarm()
            self.service_manager.update_foreground_notification_info()
            self.send_action(DM.ACTION.UPDATE_TASKS, task_data)
            self.send_action(DM.ACTION.STOP_ALARM)
            
            if action.endswith(DM.ACTION.OPEN_APP):
                self.service_manager._open_app()
        
        return Service.START_STICKY

    def send_action(self, action: str, task_data: dict | None = None) -> None:
        """Send a broadcast action (both internal and to app)"""
        if not self.context:
            logger.error("Cannot send action - no context available")
            return
        
        if not DM.validate_action(action):
            logger.error(f"Invalid action: {action}")
            return

        try:
            # Special handling for OPEN_APP action
            if action == DM.ACTION.OPEN_APP:
                self.service_manager._open_app()
                return

            intent = Intent()
            intent.setAction(f"{self.package_name}.{action}")
            intent.setPackage(self.package_name)
            intent.putExtra(DM.ACTION_TARGET.TARGET, AndroidString(DM.ACTION_TARGET.APP))

            # Add task data if provided
            if task_data:
                logger.debug(f"Adding task_data to intent: {task_data}")
                # Ensure task_id is properly set
                if "task_id" in task_data:
                    task_id = AndroidString(str(task_data["task_id"]))
                    intent.putExtra("task_id", task_id)
                    logger.debug(f"Added task_id extra: {task_id}")
                
                # Add other data
                if "notification_type" in task_data:
                    notif_type = AndroidString(str(task_data["notification_type"]))
                    intent.putExtra("notification_type", notif_type)
                    logger.debug(f"Added notification_type extra: {notif_type}")
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast action: {action} with data: {task_data}")
        except Exception as e:
            logger.error(f"Error sending broadcast action: {e}", exc_info=True)
    
    def _update_tasks_action(self) -> None:
        """Handle the UPDATE_TASKS action"""
        try:
            # First refresh tasks and clear expired task
            self.expiry_manager._refresh_tasks()  # This will clear expired task and refresh everything
            
            # Then update notification
            self.service_manager.update_foreground_notification_info()
            logger.trace("Updated Tasks and foreground notification through service action")
        
        except Exception as e:
            logger.error(f"Error handling UPDATE_TASKS: {e}")
    
    def _stop_alarm_action(self) -> None:
        """Handle the STOP_ALARM action"""
        try:
            self.audio_manager.stop_alarm()
            logger.trace("Stopped alarm through service action")
        
        except Exception as e:
            logger.error(f"Error handling STOP_ALARM: {e}")
