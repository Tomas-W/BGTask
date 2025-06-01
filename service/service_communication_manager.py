from android.broadcast import BroadcastReceiver # type: ignore
from jnius import autoclass  # type: ignore
from service.service_device_manager import DM
from src.utils.logger import logger



AndroidString = autoclass("java.lang.String")
Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")


class ServiceCommunicationManager:
    """Manages communication from the service to the app through broadcast actions"""
    
    def __init__(self, service_manager):
        self.service_manager = service_manager
        self.expiry_manager = service_manager.expiry_manager
        self.audio_manager = service_manager.audio_manager

        self.context = None
        self.package_name = None
        self.receiver = None

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
        """Initialize broadcast receiver for app messages"""
        try:
            if not self.context:
                logger.error("Cannot initialize receiver - no context available")
                return

            # Define actions to listen for
            actions = [
                f"{self.package_name}.{DM.ACTION.STOP_ALARM}",
                f"{self.package_name}.{DM.ACTION.UPDATE_TASKS}",
            ]

            # Create and start the receiver - remove package and exported parameters
            self.receiver = BroadcastReceiver(
                self._receiver_callback,
                actions=actions
            )
            self.receiver.start()
            logger.debug(f"Started broadcast receiver for actions: {actions}")
            
        except Exception as e:
            logger.error(f"Error initializing broadcast receiver: {e}")

    def _receiver_callback(self, context, intent) -> None:
        """Handle messages received from the app"""
        try:
            action = intent.getAction()
            if not action:
                logger.error("Received intent with null action")
                return
                
            pure_action = action.split(".")[-1]
            logger.debug(f"ServiceCommunicationManager received action: {pure_action}")
            
            if pure_action == DM.ACTION.UPDATE_TASKS:
                self._handle_update_tasks()
            elif pure_action == DM.ACTION.STOP_ALARM:
                self._handle_stop_alarm()
                
        except Exception as e:
            logger.error(f"Error in broadcast receiver callback: {e}")

    def _handle_update_tasks(self) -> None:
        """Handle the UPDATE_TASKS action"""
        try:
            # First refresh tasks
            self.expiry_manager.refresh_active_tasks()
            self.expiry_manager.refresh_current_task()
            
            # Then update notification
            self.service_manager.update_foreground_notification_info()
            logger.trace("Updated Tasks and foreground notification through service action")
        
        except Exception as e:
            logger.error(f"Error handling UPDATE_TASKS: {e}")
    
    def _handle_stop_alarm(self) -> None:
        """Handle the STOP_ALARM action"""
        try:
            self.audio_manager.stop_alarm()
            logger.trace("Stopped alarm through service action")
        
        except Exception as e:
            logger.error(f"Error handling STOP_ALARM: {e}")

    def send_action(self, action: str, task_data: dict | None = None) -> None:
        """Send a broadcast action from the service to the app"""
        if not self.context:
            logger.error("Cannot send action - no context available")
            return

        try:
            intent = Intent()
            intent.setAction(f"{self.package_name}.{action}")
            intent.setPackage(self.package_name)
            
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

