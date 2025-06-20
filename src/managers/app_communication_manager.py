from typing import Any, TYPE_CHECKING
from datetime import datetime

from kivy.clock import Clock

from managers.device.device_manager import DM
from src.utils.wrappers import android_only_class
from src.utils.logger import logger

try:
    from android.broadcast import BroadcastReceiver  # type: ignore
    from jnius import autoclass                      # type: ignore

    AndroidString = autoclass("java.lang.String")
    Intent = autoclass("android.content.Intent")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

except Exception as e:
    pass

if TYPE_CHECKING:
    from main import TaskApp
    from src.managers.app_expiry_manager import AppExpiryManager
    from src.managers.app_task_manager import TaskManager 
    from src.managers.app_audio_manager import AppAudioManager


@android_only_class()
class AppCommunicationManager():
    """
    Manages communication between the App and the Service.
    - Sends actions to the Service
    - Receives actions from the Service
    - Receiver listens for ACTION_TARGET: APP
    """
    def __init__(self,
                 app: "TaskApp"):
        self.app = app
        self.expiry_manager: "AppExpiryManager" = app.expiry_manager
        self.task_manager: "TaskManager" = app.task_manager
        self.audio_manager: "AppAudioManager" = app.audio_manager

        self.context: Any | None = None
        self.package_name: str | None = None
        self.receiver: BroadcastReceiver | None = None

        self._init_context()
        self._init_receiver()

        self.send_action(DM.ACTION.STOP_ALARM)
    
    def _init_context(self) -> None:
        """Initializes the App context and package name."""
        try:
            if hasattr(PythonActivity, "mActivity") and PythonActivity.mActivity:
                self.context = PythonActivity.mActivity
                self.package_name = self.context.getPackageName()
            else:
                logger.error("Error initializing App context - activity context not available.")
        
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
                    
        except Exception as e:
            logger.error(f"Error initializing broadcast receiver: {e}")

    def _receiver_callback(self, context: Any, intent: Any) -> None:
        """
        Handles actions received from the broadcast receiver.
        - Returns early if the target is not ACTION_TARGET.APP
        - Extracts pure action from intent
        - Extracts task_id from the intent if present
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
            # Extract task_id from intent extras
            task_id = intent.getStringExtra("task_id")
            # Schedule the actions effect
            Clock.schedule_once(
                lambda dt: self.handle_action(pure_action, task_id), 
                0
            )
        except Exception as e:
            logger.error(f"Error receiving Service action: {e}")

    def handle_action(self, pure_action: str, task_id: str | None = None) -> None:
        """
        Calls the appropriate method based on the action received from the receiver.
        """
        try:
            if pure_action == DM.ACTION.STOP_ALARM:
                self._stop_alarm_action()
            
            elif pure_action == DM.ACTION.UPDATE_TASKS:
                self._update_tasks_action(task_id)
        
        except Exception as e:
            logger.error(f"Error handling service action: {e}")

    def send_action(self, action: str, task_id: str | None = None) -> None:
        """
        Send a broadcast action with ACTION_TARGET: SERVICE.
        """
        if not DM.validate_action(action):
            logger.error(f"Error sending action, invalid action: {action}")
            return

        try:
            if not self.context:
                logger.error("Error sending action, no context available")
                return
            
            intent = Intent()
            intent.setAction(f"{self.package_name}.{action}")
            intent.setPackage(self.package_name)
            # Flag action to be received only by the Service
            intent.putExtra(DM.ACTION_TARGET.TARGET,
                            AndroidString(DM.ACTION_TARGET.SERVICE))
            
            # Add task_id if provided
            if task_id:
                intent.putExtra("task_id", AndroidString(task_id))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast action: {action} with task_id: {DM.get_task_id_log(task_id)}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast action: {e}")
    
    def _get_pure_action(self, intent: Any) -> str | None:
        """Extracts and returns the pure action from the intent, or None."""
        action = intent.getAction()
        if not action:
            return None
        
        pure_action = action.split(".")[-1]
        return pure_action
    
    def _stop_alarm_action(self) -> None:
        """Stops the App alarm through the AudioManager."""
        self.audio_manager.stop_alarm()
        
    def _update_tasks_action(self, task_id: str | None = None) -> None:
        """
        Refreshes ExpiryManager, TaskManager Tasks and updates App UI.
        Task_id is only provided after snooze or cancel from a Service notification,
         for invalidation of cached Task data.
        """
        # Update AppExpiryManager
        self.task_manager.expiry_manager._refresh_tasks()
        # Update TaskManager
        self.task_manager.refresh_task_groups()
        
        # Update HomeScreen
        if task_id:
            task = self.task_manager.get_task_by_id_(task_id)
            if task:
                date_key = task.get_date_key()
                self.task_manager.update_home_after_changes(date_key)
        
        # No task_id or Task, use today's date
        self.task_manager.update_home_after_changes(datetime.now().date().isoformat())
