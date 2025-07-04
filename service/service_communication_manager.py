from typing import Any, TYPE_CHECKING

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore

from managers.device.device_manager import DM

from src.utils.logger import logger

AndroidString = autoclass("java.lang.String")
BuildVersion = autoclass("android.os.Build$VERSION")
Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")
PendingIntent = autoclass("android.app.PendingIntent")
Context = autoclass("android.content.Context")

if TYPE_CHECKING:
    from service.service_manager import ServiceManager
    from service.service_audio_manager import ServiceAudioManager
    from service.service_expiry_manager import ServiceExpiryManager
    from service.service_notification_manager import ServiceNotificationManager


class ServiceCommunicationManager:
    """
    Manages all communication within the Service and with the App.
    - Sends actions to the App
    - Receives actions from the App and Service
    - Receiver listens for ACTION_TARGET: SERVICE and APP
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

        self.service_actions: list[str] = [
            DM.ACTION.SNOOZE_A,
            DM.ACTION.SNOOZE_B,
            DM.ACTION.CANCEL,
        ]
        self.app_actions: list[str] = [
            DM.ACTION.UPDATE_TASKS,
            DM.ACTION.STOP_ALARM,
            DM.ACTION.REMOVE_TASK_NOTIFICATIONS,
        ]
        self.boot_actions: list[str] = [
            DM.ACTION.BOOT_COMPLETED,
            DM.ACTION.RESTART_SERVICE,
        ]
        self.all_actions: list[str] = self.service_actions + self.app_actions + self.boot_actions

        self._init_context()
        self._init_receiver()
    
    def _init_context(self) -> None:
        """Initializes the Service context and package name."""
        try:
            if hasattr(PythonService, "mService") and PythonService.mService:
                self.context = PythonService.mService.getApplicationContext()
                self.package_name = self.context.getPackageName()
            else:
                logger.error("Error initializing Service context - service context not available.")
        
        except Exception as e:
            logger.error(f"Error initializing Service context: {e}")

    def _init_receiver(self) -> None:
        """
        Initializes the broadcast receiver for App and Service actions.
        - Does not listen for ACTION_TARGETs - accepts all actions
        - Listens for ACTION: SNOOZE_A | SNOOZE_B | CANCEL
        - Listens for ACTION: STOP_ALARM | UPDATE_TASKS | REMOVE_TASK_NOTIFICATIONS
        - Listens for ACTION: BOOT_COMPLETED | RESTART_SERVICE
        """
        try:
            if not self.context:
                logger.error("Error initializing receiver - no context available")
                return

            # Actions to listen for
            actions = self._get_receiver_actions()
            # Create and start the receiver
            self.receiver = BroadcastReceiver(
                self._receiver_callback,
                actions=actions
            )
            self.receiver.start()

        except Exception as e:
            logger.error(f"Error initializing broadcast receiver: {e}")
    
    def _get_receiver_actions(self) -> list[str]:
        """Converts and returns pure actions to receiver actions."""
        actions = []
        # Add package-prefixed actions
        for action in self.all_actions:
            if action != DM.ACTION.BOOT_COMPLETED:
                actions.append(f"{self.package_name}.{action}")
        
        # Add boot action
        actions.append(f"{DM.ACTION.BOOT_ACTION}.{DM.ACTION.BOOT_COMPLETED}")
        return actions

    def _receiver_callback(self, context: Any, intent: Any) -> None:
        """
        Handles actions received through the broadcast receiver.
        Service listens to all actions so no need to check target.
        - Extracts pure action from intent
        - Routes to appropriate handler based on action
        """
        try:
            pure_action = self._get_pure_action(intent)
            if not pure_action:
                logger.error("Error receiving callback - intent with null action")
                return
            
            logger.debug(f"ServiceCommunicationManager received intent with action: {pure_action}")
            task_id = self._get_task_id(intent, pure_action)
            self.handle_action(intent,pure_action, task_id)
                
        except Exception as e:
            logger.error(f"Error in broadcast receiver callback: {e}")

    def handle_action(self, intent: Any, pure_action: str, task_id: str | None = None) -> int:
        """
        Processes the action through both service and app handlers.
        - Service handler processes service actions (snooze, cancel, etc.)
        - App handler processes app actions (update tasks, stop alarm)
        - Handles restart service action separately
        All actions require cancelling all notifications.
        """
        # Check boot and restart actions
        if pure_action in self.boot_actions:
            self._handle_boot_action(pure_action)
            logger.debug("ServiceCommunicationManager received boot action")
            return Service.START_STICKY

        # Cancel all notifications for any non-boot action
        self.notification_manager.cancel_all_notifications()

        # Check Service actions
        if self._is_service_action(pure_action):
            if not task_id:
                logger.error(f"Error getting task_id from action: {pure_action}")
                return Service.START_STICKY
            
            self._handle_service_action(pure_action, task_id)
            return Service.START_STICKY

        # Check App actions
        if self._is_app_action(pure_action):
            self._handle_app_action(pure_action)
            return Service.START_STICKY
        
        logger.error(f"Error handling action: {pure_action}")
        return Service.START_STICKY
    
    def _is_service_action(self, pure_action: str) -> bool:
        """Checks if the action is a Service action."""
        return any(pure_action.endswith(action) for action in self.service_actions)
    
    def _is_app_action(self, pure_action: str) -> bool:
        """Checks if the action is an App action."""
        return any(pure_action.endswith(action) for action in self.app_actions)

    def _handle_boot_action(self, pure_action: str) -> None:
        """Handles boot actions."""
        from service.main import start_service
        start_service()

    def _handle_service_action(self, pure_action: str, task_id: str) -> int:
        """
        Handles service actions (snooze, cancel, etc.) and notification actions.
        - Processes snooze/cancel actions from notifications
        - Updates service state and sends actions to App
        """
        logger.debug(f"_handle_service_action: {pure_action}")
        # Snooze
        if pure_action == DM.ACTION.SNOOZE_A or pure_action == DM.ACTION.SNOOZE_B:
            self._snooze_action(pure_action, task_id)
        
        # Cancel and open app
        elif pure_action == DM.ACTION.CANCEL:
            self._cancel_action(pure_action, task_id)
        
        return Service.START_STICKY

    def _handle_app_action(self, pure_action: str) -> int:
        """
        Handles app actions (update tasks, stop alarm).
        - Processes app communication actions
        - Updates service state as needed
        """
        # Update tasks
        if pure_action.endswith(DM.ACTION.UPDATE_TASKS):
            self._update_tasks_action()
        
        # Stop alarm
        elif pure_action.endswith(DM.ACTION.STOP_ALARM):
            self._stop_alarm_action()
        
        # Remove task notifications
        elif pure_action.endswith(DM.ACTION.REMOVE_TASK_NOTIFICATIONS):
            self._remove_task_notifications_action()

        return Service.START_STICKY

    def send_action(self, action: str, task_id: str | None = None) -> None:
        """
        Sends a broadcast action with ACTION_TARGET: APP and SERVICE.
        - Validates action before sending
        - Adds task_id to intent if provided
        """
        if not self.context:
            logger.error("Error sending action - no context available")
            return
        
        if not DM.validate_action(action):
            logger.error(f"Error sending action - invalid action: {action}")
            return

        try:
            intent = self._get_send_action_intent(action)
            if task_id:
                intent.putExtra("task_id", AndroidString(task_id))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast action: {action} with task_id: {DM.get_task_id_log(task_id)}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast action: {e}", exc_info=True)
    
    def _get_send_action_intent(self, action: str) -> Any:
        """Returns an intent for the given action."""
        intent = Intent()
        intent.setAction(f"{self.package_name}.{action}")
        intent.setPackage(self.package_name)
        intent.putExtra(DM.ACTION_TARGET.TARGET, AndroidString(DM.ACTION_TARGET.APP))
        return intent
    
    def _get_task_id(self, intent: Any, action: str | None = None) -> str | None:
        """
        Extracts and returns task_id from the intent extras, or None.
        Falls back to current task's ID only for service actions that require it.
        """
        task_id = intent.getStringExtra("task_id")        
        if task_id:
            return task_id
        
        # Fallback to current Task's ID
        if action and any(action.endswith(a) for a in self.service_actions):
            if self.expiry_manager.current_task:
                logger.error(f"Error getting task_id from intent - using current task_id: {self.expiry_manager.current_task.task_id}")
                return self.expiry_manager.current_task.task_id
        
        return None

    def _snooze_action(self, action: str, task_id: str) -> None:
        """Handles snooze actions from notifications."""
        logger.trace(f"Handling snooze action for Task with ID: {DM.get_task_id_log(task_id)}")
        try:
            # Service side
            self.expiry_manager.snooze_task(action, task_id)
            self.service_manager.update_foreground_notification_info()
            # App side
            self.send_action(DM.ACTION.UPDATE_TASKS, task_id)

        except Exception as e:
            logger.error(f"Error handling snooze action: {e}")

    def _cancel_action(self, action: str, task_id: str) -> None:
        """
        Handles cancel and open app actions from notifications.
        Same functionality for both actions, except different snooze times.
        """
        logger.trace(f"Handling cancel action for Task with ID: {DM.get_task_id_log(task_id)}")
        try:
            # Service side
            self.expiry_manager.cancel_task(task_id)
            self.service_manager.update_foreground_notification_info()
            # App side
            self.send_action(DM.ACTION.UPDATE_TASKS, task_id)

        except Exception as e:
            logger.error(f"Error handling cancel action: {e}")
    
    def _update_tasks_action(self) -> None:
        """Refreshes ExpiryManager Tasks and updates foreground notification."""
        logger.trace("Handling update tasks action")
        self.expiry_manager._refresh_tasks()
        self.service_manager.update_foreground_notification_info()
        logger.trace("Updated Tasks and foreground notification through service action")
    
    def _stop_alarm_action(self) -> None:
        """Stops the Service alarm through the AudioManager."""
        logger.trace("Handling stop alarm action")
        self.audio_manager.stop_alarm()

    def _remove_task_notifications_action(self) -> None:
        """Removes all task notifications."""
        logger.trace("Handling remove task notifications action")
        self.notification_manager.cancel_all_notifications()
    
    def _get_pure_action(self, intent: Any) -> str | None:
        """Extracts and returns the pure action from the intent, or None."""
        action = intent.getAction()
        if not action:
            return None
        
        pure_action = action.split(".")[-1]
        return pure_action
