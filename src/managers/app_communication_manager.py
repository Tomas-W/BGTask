from typing import Any, TYPE_CHECKING

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore
from kivy.clock import Clock

from src.managers.app_device_manager import DM
from src.utils.logger import logger

AndroidString = autoclass("java.lang.String")

if TYPE_CHECKING:
    from src.managers.app_task_manager import TaskManager 
    from src.managers.app_expiry_manager import AppExpiryManager


class AppCommunicationManager():
    """
    Manages communication between the App and the Service.
    - Sends actions to the Service
    - Receives actions from the Service
    """
    def __init__(self,
                 task_manager: "TaskManager",
                 expiry_manager: "AppExpiryManager"):
        
        self.task_manager: "TaskManager" = task_manager
        self.expiry_manager: "AppExpiryManager" = expiry_manager
        self.expiry_manager.bind(on_task_expired_remove_task_notifications=self._remove_notifications)
        
        self.context: Any | None = None
        self.package_name: str | None = None
        self.receiver: BroadcastReceiver | None = None

        self._init_context()
        self._init_receiver()

    def _init_context(self) -> None:
        """Initializes the App context."""
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            
            if hasattr(PythonActivity, "mActivity") and PythonActivity.mActivity:
                self.context = PythonActivity.mActivity
                self.package_name = self.context.getPackageName()
                logger.debug("Initialized AppCommunicationManager.")
            else:
                logger.error("Error initializing context - activity context not available.")
        
        except Exception as e:
            logger.error(f"Error initializing App context: {e}")

    def _init_receiver(self) -> None:
        """Initializes the broadcast receiver for Service actions."""
        try:
            if not self.context:
                logger.error("Error initializing receiver - no context available")
                return
            
            # Actions to listen for
            actions = [
                f"{self.package_name}.{DM.ACTION.STOP_ALARM}",
                f"{self.package_name}.{DM.ACTION.UPDATE_TASKS}",
            ]

            # Create and start receiver
            self.receiver = BroadcastReceiver(
                self._receiver_callback,
                actions=actions
            )
            self.receiver.start()
            logger.debug(f"Started broadcast receiver for actions: {actions}")
            
        except Exception as e:
            logger.error(f"Error initializing broadcast receiver: {e}")

    def _receiver_callback(self, context: Any, intent: Any) -> None:
        """Handles actions received from the Service."""
        try:
            target = intent.getStringExtra(DM.ACTION_TARGET.TARGET)
            logger.debug(f"AppCommunicationManager received intent with target: {target}")
            if target != DM.ACTION_TARGET.APP:
                return
            
            action = intent.getAction()
            if not action:
                logger.error("Received intent with null action")
                return
            
            pure_action = action.split(".")[-1]
            logger.debug(f"Received service action: {pure_action}")
            
            # Extract Task data from intent extras
            task_data = None
            if intent.hasExtra("task_id"):
                task_id = intent.getStringExtra("task_id")
                if task_id:
                    task_data = {
                        "task_id": task_id,
                        "notification_type": intent.getStringExtra("notification_type")
                    }
            
            # Schedule the actions effect
            Clock.schedule_once(
                lambda dt: self.handle_service_action(pure_action, task_data), 
                0
            )
        except Exception as e:
            logger.error(f"Error receiving Service action: {e}")

    def handle_service_action(self, action: str, task_data: dict | None = None) -> None:
        """Handles actions received from the Service."""
        try:
            if action == DM.ACTION.STOP_ALARM:
                self._stop_alarm_action()
            
            elif action == DM.ACTION.UPDATE_TASKS:
                self._update_tasks_action(task_data)
            
        except Exception as e:
            logger.error(f"Error handling service action: {e}")

    def send_action(self, action: str):
        """Send a broadcast action to the service"""
        if not DM.is_android:
            logger.debug("Not Android, skipping action")
            return
        
        if not DM.validate_action(action):
            logger.error(f"Invalid action: {action}")
            return

        try:
            if not self.context:
                logger.error("Cannot send action - no context available")
                return

            Intent = autoclass("android.content.Intent")
            
            intent = Intent()
            intent.setAction(f"{self.package_name}.{action}")
            intent.setPackage(self.package_name)
            # Use AndroidString for the target extra
            intent.putExtra(DM.ACTION_TARGET.TARGET, AndroidString(DM.ACTION_TARGET.SERVICE))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast action: {action}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast action: {e}")
    
    def _remove_notifications(self, *args, **kwargs) -> None:
        """Remove notifications from the app"""
        self.send_action(DM.ACTION.REMOVE_TASK_NOTIFICATIONS)
    
    def _stop_alarm_action(self) -> None:
        """
        Handles the STOP_ALARM action.
        - Stops the alarm
        """
        self.expiry_manager.dispatch("on_task_cancelled_stop_alarm")
    
    def _update_tasks_action(self, task_data: dict | None = None) -> None:
        """
        Handles the UPDATE_TASKS action.
        - Refreshes ExpiryManager tasks
        - Refreshes TaskManager tasks
        - Refreshes HomeScreen
        - Refreshes StartScreen
        """
        # Update AppExpiryManager
        self.task_manager.expiry_manager._refresh_tasks()
        # Update TaskManager
        self.task_manager.tasks_by_date = self.task_manager._load_tasks_by_date()
        self.task_manager.sort_active_tasks()
        
        if task_data:
            task = self.task_manager.get_task_by_id(task_data["task_id"])
            if task:
                # Send Task for cache invalidation
                self.task_manager.dispatch(
                    "on_task_edit_refresh_home_screen", 
                    task=task
                )
            self.task_manager.dispatch(
                "on_task_edit_refresh_start_screen"
            )
        else:
            # Fallback to regular dispatch without task data
            logger.error("FALLBACK TO REGULAR DISPATCH WITHOUT TASK DATA")
            self.task_manager.dispatch("on_task_edit_refresh_home_screen")
            self.task_manager.dispatch("on_task_edit_refresh_start_screen")