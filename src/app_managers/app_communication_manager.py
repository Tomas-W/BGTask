from typing import Any, TYPE_CHECKING

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
    Context = autoclass("android.content.Context")
    RunningAppProcessInfo = autoclass("android.app.ActivityManager$RunningAppProcessInfo")

except Exception as e:
    pass

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.app_expiry_manager import AppExpiryManager
    from src.app_managers.app_task_manager import TaskManager 
    from src.app_managers.app_audio_manager import AppAudioManager


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
                f"{self.package_name}.{DM.ACTION.LOCATION_RESPONSE}",
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
        - Passes intent to action handler for data extraction
        """
        try:
            target = intent.getStringExtra(DM.ACTION_TARGET.TARGET)
            if target != DM.ACTION_TARGET.APP:
                return
            
            pure_action = self._get_pure_action(intent)
            if not pure_action:
                logger.error("Error receiving callback - intent with null action")
                return
            
            logger.debug(f"AppCommunicationManager received intent with action: {pure_action}")
            self.handle_action(pure_action, intent)
                
        except Exception as e:
            logger.error(f"Error in broadcast receiver callback: {e}")
    def handle_action(self, pure_action: str, intent: Any) -> None:
        """
        Calls the appropriate method based on the action received from the receiver.
        """
        try:
            if pure_action == DM.ACTION.STOP_ALARM:
                self._stop_alarm_action()
            
            elif pure_action == DM.ACTION.UPDATE_TASKS:
                self._update_tasks_action(intent)
            
            elif pure_action == DM.ACTION.LOCATION_RESPONSE:
                self._location_response_action(intent)
        
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

    def send_gps_monitoring_action(self, target_lat: float, target_lon: float, alert_distance: float = None) -> None:
        """
        Send GPS monitoring action with target coordinates to service.
        """
        if not DM.validate_action(DM.ACTION.START_LOCATION_MONITORING):
            logger.error("Error sending GPS monitoring action, invalid action")
            return

        try:
            if not self.context:
                logger.error("Error sending GPS monitoring action, no context available")
                return
            
            intent = Intent()
            intent.setAction(f"{self.package_name}.{DM.ACTION.START_LOCATION_MONITORING}")
            intent.setPackage(self.package_name)
            # Flag action to be received only by the Service
            intent.putExtra(DM.ACTION_TARGET.TARGET,
                            AndroidString(DM.ACTION_TARGET.SERVICE))
            
            # Add GPS coordinates
            intent.putExtra("target_lat", AndroidString(str(target_lat)))
            intent.putExtra("target_lon", AndroidString(str(target_lon)))
            if alert_distance is not None:
                intent.putExtra("alert_distance", AndroidString(str(alert_distance)))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Sent GPS monitoring action for coordinates: {target_lat}, {target_lon}")
        
        except Exception as e:
            logger.error(f"Error sending GPS monitoring action: {e}")
    
    def _get_pure_action(self, intent: Any) -> str | None:
        """Extracts and returns the pure action from the intent, or None."""
        action = intent.getAction()
        if not action:
            return None
        
        pure_action = action.split(".")[-1]
        return pure_action
    
    def _get_task_id_from_intent(self, intent: Any) -> str | None:
        """Extracts and returns the task_id from the intent, or None."""
        try:
            return intent.getStringExtra("task_id")
        except Exception as e:
            logger.error(f"Error extracting task_id from intent: {e}")
            return None
    
    def _get_location_data_from_intent(self, intent: Any) -> dict:
        """Extracts and returns location data from the intent."""
        try:
            success = intent.getStringExtra("success")
            if success == "true":
                lat_str = intent.getStringExtra("latitude")
                lon_str = intent.getStringExtra("longitude")
                if lat_str and lon_str:
                    return {
                        "latitude": float(lat_str),
                        "longitude": float(lon_str),
                        "success": True
                    }
                else:
                    return {"success": False, "reason": "missing_coordinates"}
            else:
                return {"success": False, "reason": "service_unavailable"}
        except Exception as e:
            logger.error(f"Error extracting location data from intent: {e}")
            return {"success": False, "reason": "extraction_error"}
    
    def _stop_alarm_action(self) -> None:
        """Stops the App alarm through the AudioManager."""
        self.audio_manager.stop_alarm()
        
    def _update_tasks_action(self, intent: Any) -> None:
        """
        Refreshes ExpiryManager, TaskManager Tasks and updates App UI.
        Task_id is only provided after snooze or cancel from a Service notification,
         for invalidation of cached Task data.
        """
        task_id = self._get_task_id_from_intent(intent)
        
        self.task_manager.expiry_manager._refresh_tasks()
        self.task_manager.refresh_task_groups()
        
        task = self.task_manager.get_task_by_id(task_id)
        date_key = task.get_date_key()

        if self._is_app_in_foreground():
            Clock.schedule_once(lambda dt: self.task_manager.update_home_after_changes(date_key), 0)
            Clock.schedule_once(lambda dt: self.app.get_screen(DM.SCREEN.HOME).scroll_to_task(task), 0.15)
            return
        
        # If app is in background, set _need_updates to task_id
        self.app._need_updates = task_id
        return
    
    def _is_app_in_foreground(self) -> bool:
        """Returns True if the App is currently in the foreground."""
        try:
            if not self.context:
                return False
            
            # Get ActivityManager service
            activity_manager = self.context.getSystemService(Context.ACTIVITY_SERVICE)
            if not activity_manager:
                return False
            
            # Get running App processes
            running_apps = activity_manager.getRunningAppProcesses()
            if not running_apps:
                return False
            
            # Check if in foreground
            for process in running_apps:
                if (process.processName == self.package_name and 
                    process.importance == RunningAppProcessInfo.IMPORTANCE_FOREGROUND):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking app foreground state: {e}")
            return False
    
    def _location_response_action(self, intent: Any) -> None:
        """Handles location response from service."""
        try:
            location_data = self._get_location_data_from_intent(intent)
            
            if location_data.get("success"):
                lat = location_data["latitude"]
                lon = location_data["longitude"]
                logger.info(f"Received location from service: {lat}, {lon}")
                
                # If map screen is active, update it
                current_screen = self.app.screen_manager.current
                if current_screen == DM.SCREEN.MAP:
                    map_screen = self.app.get_screen(DM.SCREEN.MAP)
                    Clock.schedule_once(lambda dt: map_screen.handle_location_response(lat, lon), 0)
                    
            else:
                reason = location_data.get("reason", "unknown")
                logger.warning(f"Service could not provide location: {reason}")
                
                # If map screen is active, notify of failure
                current_screen = self.app.screen_manager.current
                if current_screen == DM.SCREEN.MAP:
                    map_screen = self.app.get_screen(DM.SCREEN.MAP)
                    Clock.schedule_once(lambda dt: map_screen.handle_location_response(None, None), 0)
                    
        except Exception as e:
            logger.error(f"Error handling location response: {e}")
    
