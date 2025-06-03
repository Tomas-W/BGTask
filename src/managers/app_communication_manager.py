from typing import Any, TYPE_CHECKING

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore
from kivy.clock import Clock

from src.managers.app_device_manager import DM
from src.utils.logger import logger

AndroidString = autoclass("java.lang.String")
Intent = autoclass("android.content.Intent")
PythonActivity = autoclass("org.kivy.android.PythonActivity")

if TYPE_CHECKING:
    from src.managers.app_task_manager import TaskManager 
    from src.managers.app_expiry_manager import AppExpiryManager
    from managers.tasks.task_manager_utils import Task

class AppCommunicationManager():
    """
    Manages communication between the App and the Service.
    - Sends actions to the Service
    - Receives actions from the Service
    - Receiver listens for ACTION_TARGET: APP
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
        """Initializes the App context and package name."""
        try:
            if hasattr(PythonActivity, "mActivity") and PythonActivity.mActivity:
                self.context = PythonActivity.mActivity
                self.package_name = self.context.getPackageName()
                logger.debug("Initialized AppCommunicationManager.")
            else:
                logger.error("Error initializing context - activity context not available.")
        
        except Exception as e:
            logger.error(f"Error initializing App context: {e}")

    def _init_receiver(self) -> None:
        """
        Initializes the broadcast receiver for Service actions.
        - Listens for ACTION_TARGET: APP
        - Listens for ACTION: STOP_ALARM | UPDATE_TASKS
        """
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
        """
        Handles actions received from the broadcast receiver.
        - Returns early if the target is not ACTION_TARGET.APP
        - Extracts pure action from intent
        - Extracts task_data from the intent if present
        - Schedules the actions effect handler
        """
        try:
            target = intent.getStringExtra(DM.ACTION_TARGET.TARGET)
            if target != DM.ACTION_TARGET.APP:
                return
            
            pure_action = self._get_pure_action(intent)
            if not pure_action:
                logger.error("Error receiving callback - intent with null action")
                return
            
            logger.debug(f"AppCommunicationManager received intent with target: {target} and action: {pure_action}")
            
            # Extract Task data from intent extras
            task_data = self._get_task_data(intent)
            
            # Schedule the actions effect
            Clock.schedule_once(
                lambda dt: self.handle_action(pure_action, task_data), 
                0
            )
        except Exception as e:
            logger.error(f"Error receiving Service action: {e}")

    def handle_action(self, action: str, task_data: dict | None = None) -> None:
        """
        Calls the appropriate method based on the action received from the receiver.
        """
        try:
            if action == DM.ACTION.STOP_ALARM:
                self._stop_alarm_action()
            
            elif action == DM.ACTION.UPDATE_TASKS:
                self._update_tasks_action(task_data)
            
        except Exception as e:
            logger.error(f"Error handling service action: {e}")

    def send_action(self, action: str):
        """
        Send a broadcast action with ACTION_TARGET: SERVICE.
        """
        if not DM.is_android:
            logger.debug("Not Android, skipping action.")
            return
        
        if not DM.validate_action(action):
            logger.error(f"Invalid action: {action}")
            return

        try:
            if not self.context:
                logger.error("Cannot send action - no context available")
                return
            
            intent = Intent()
            intent.setAction(f"{self.package_name}.{action}")
            intent.setPackage(self.package_name)
            # Flag action to be received only by the Service
            intent.putExtra(DM.ACTION_TARGET.TARGET,
                            AndroidString(DM.ACTION_TARGET.SERVICE))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast action: {action}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast action: {e}")
    
    def _get_pure_action(self, intent: Any) -> str | None:
        """Extracts and returns the pure action from the intent, or None."""
        action = intent.getAction()
        if not action:
            return None
        
        pure_action = action.split(".")[-1]
        return pure_action
    
    def _get_task_data(self, intent: Any) -> dict | None:
        """Extracts and returns task_data from the intent extras, or None."""
        task_data = None
        if intent.hasExtra("task_id"):
            task_id = intent.getStringExtra("task_id")
            if task_id:
                task_data = {"task_id": task_id,
                             "notification_type": intent.getStringExtra("notification_type")}
        return task_data

    def _get_task(self, task_data: dict | None = None) -> "Task | None":
        """Extracts and returns Task object from task_data, or None."""
        if task_data:
            task_id = task_data["task_id"]
            if task_id:
                return self.task_manager.get_task_by_id(task_id)
        
        return None
    
    def _remove_notifications(self, *args, **kwargs) -> None:
        """Sends action to Service to remove Task notifications."""
        self.send_action(DM.ACTION.REMOVE_TASK_NOTIFICATIONS)
    
    def _stop_alarm_action(self) -> None:
        """Stops the App alarm through the AudioManager."""
        self.expiry_manager.dispatch("on_task_cancelled_stop_alarm")
    
    def _update_tasks_action(self, task_data: dict | None = None) -> None:
        """
        Refreshes ExpiryManager, TaskManager Tasks and updates App UI.
        Task data is only provided after snooze or cancel from a Service notification,
         for invalidation of cached Task data.
        """
        # Update AppExpiryManager
        self.task_manager.expiry_manager._refresh_tasks()
        # Update TaskManager
        self.task_manager.tasks_by_date = self.task_manager._load_tasks_by_date()
        self.task_manager.sort_active_tasks()
        
        # If Task, a Task was snoozed or cancelled from a Service notification
        # Task cache must be invalidated in HomeScreen
        # Otherwise, Task is None
        task = self._get_task(task_data)

        # Refresh HomeScreen
        self.task_manager.dispatch(
            "on_task_edit_refresh_home_screen", 
            task=task
        )
        # Refresh StartScreen
        self.task_manager.dispatch(
            "on_task_edit_refresh_start_screen"
        )