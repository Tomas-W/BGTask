from typing import TYPE_CHECKING
from threading import Thread

from src.managers.app_device_manager import DM
from src.utils.logger import logger
from kivy.clock import Clock

if TYPE_CHECKING:
    from src.managers.app_task_manager import TaskManager

class AppCommunicationManager:
    def __init__(self, task_manager: "TaskManager"):
        self.task_manager = task_manager
        self.expiry_manager = task_manager.expiry_manager
        self.receiver = None
        self._init_receiver()

    def _init_receiver(self) -> None:
        """Initialize broadcast receiver for service messages"""
        try:
            from jnius import autoclass                      # type: ignore
            from android.broadcast import BroadcastReceiver  # type: ignore
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            package_name = context.getPackageName()

            actions = [
                f"{package_name}.{DM.ACTION.STOP_ALARM}",
                f"{package_name}.{DM.ACTION.UPDATE_TASKS}",
            ]

            # Create and start the receiver
            self.receiver = BroadcastReceiver(
                self._receiver_callback,
                actions=actions
            )
            self.receiver.start()
            logger.debug("Started service message receiver")
        except Exception as e:
            logger.error(f"Error initializing service receiver: {e}")

    def _receiver_callback(self, context, intent) -> None:
        """Handle messages received from the app"""
        try:
            action = intent.getAction()
            if action:
                pure_action = action.split(".")[-1]
                logger.debug(f"Received service action: {pure_action}")
                
                # Debug: Log all extras from intent
                bundle = intent.getExtras()
                logger.debug("Checking intent extras bundle...")
                if bundle:
                    logger.debug("Intent extras received:")
                    keys = bundle.keySet().toArray()
                    for key in keys:
                        value = bundle.get(key)
                        logger.debug(f"  {key}: {value}")
                else:
                    logger.debug("No extras found in intent bundle")
                
                # Extract task data from intent extras
                task_data = None
                if intent.hasExtra("task_id"):
                    task_id = intent.getStringExtra("task_id")
                    logger.debug(f"Found task_id in extras: {task_id}")
                    if task_id:
                        task_data = {
                            "task_id": task_id,
                            "notification_type": intent.getStringExtra("notification_type")
                        }
                        logger.debug(f"Created task_data dictionary: {task_data}")
                else:
                    logger.debug("No task_id found in intent extras")
                
                # Schedule the action handling
                Clock.schedule_once(
                    lambda dt: self.handle_service_action(pure_action, task_data), 
                    0
                )
        except Exception as e:
            logger.error(f"Error in _receiver_callback: {e}", exc_info=True)

    def handle_service_action(self, action: str, task_data: dict | None = None) -> None:
        """Handle different types of service actions with optional task data"""
        try:
            if action == DM.ACTION.STOP_ALARM:
                self.expiry_manager.dispatch("on_task_cancelled_stop_alarm")
            
            elif action == DM.ACTION.UPDATE_TASKS:
                # Update AppExpiryManager
                self.task_manager.expiry_manager._refresh_tasks()
                # Update TaskManager
                self.task_manager.tasks_by_date = self.task_manager._load_tasks_by_date()
                self.task_manager.sort_active_tasks()
                
                # If we have task data, dispatch with it
                if task_data:
                    logger.critical(f"TASK DATA: {task_data}")
                    task = self.task_manager.get_task_by_id(task_data["task_id"])
                    logger.error(f"TRYING TO PASS THE TASK TO REFRESH_HOME_SCREEN: {task.message if task else None}")
                    if task:
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
            
        except Exception as e:
            logger.error(f"Error handling service action: {e}")

    def _validate_action(self, action: str) -> bool:
        return hasattr(DM.ACTION, action)

    def send_action(self, action: str):
        if not DM.is_android:
            logger.debug("Not Android, skipping action")
            return
        
        if not self._validate_action(action):
            logger.error(f"Invalid action: {action}")
            return

        try:
            from jnius import autoclass  # type: ignore
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            
            if not context:
                logger.error("PythonActivity.mActivity is None")
                return
                
            intent = Intent()
            full_action = f"{context.getPackageName()}.{action}"
            intent.setAction(full_action)
            intent.setPackage(context.getPackageName())
            intent.setComponent(None)  # Broadcast to all matching receivers
            context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast: {full_action}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")
