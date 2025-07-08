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
    from service.service_gps_manager import ServiceGpsManager


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
                 notification_manager: "ServiceNotificationManager",
                 gps_manager: "ServiceGpsManager"):
        
        self.service_manager: "ServiceManager" = service_manager
        self.audio_manager: "ServiceAudioManager" = audio_manager
        self.expiry_manager: "ServiceExpiryManager" = expiry_manager
        self.notification_manager: "ServiceNotificationManager" = notification_manager
        self.gps_manager: "ServiceGpsManager" = gps_manager

        self.context: Any | None = None
        self.package_name: str | None = None
        self.receiver: BroadcastReceiver | None = None

        self.service_actions: list[str] = [
            DM.ACTION.SNOOZE_A,
            DM.ACTION.SNOOZE_B,
            DM.ACTION.CANCEL,
            DM.ACTION.CANCEL_GPS,
            DM.ACTION.SKIP_GPS_TARGET,
        ]
        self.app_actions: list[str] = [
            DM.ACTION.UPDATE_TASKS,
            DM.ACTION.STOP_ALARM,
            DM.ACTION.REMOVE_TASK_NOTIFICATIONS,
            DM.ACTION.GET_LOCATION_ONCE,
            DM.ACTION.START_LOCATION_MONITORING,
            DM.ACTION.STOP_LOCATION_MONITORING,
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
            self.handle_action(intent, pure_action)
                
        except Exception as e:
            logger.error(f"Error in broadcast receiver callback: {e}")

    def handle_action(self, intent: Any, pure_action: str) -> int:
        """
        Processes the action through both service and app handlers.
        - Service handler processes service actions (snooze, cancel, etc.)
        - App handler processes app actions (update tasks, stop alarm)
        - Handles restart service action separately
        # All actions require cancelling all notifications.
        """
        # Check boot and restart actions
        if pure_action in self.boot_actions:
            self._handle_boot_action(pure_action)
            logger.debug("ServiceCommunicationManager received boot action")
            return Service.START_STICKY

        # Check Service actions
        if self._is_service_action(pure_action):
            self._handle_service_action(intent, pure_action)
            return Service.START_STICKY

        # Check App actions
        if self._is_app_action(pure_action):
            self._handle_app_action(intent, pure_action)
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

    def _handle_service_action(self, intent: Any, pure_action: str) -> int:
        """
        Handles service actions (coming from notifications)
        - Tasks: snooze, cancel
        - GPS: cancel, skip target
        """
        logger.debug(f"_handle_service_action: {pure_action}")

        # Cancel GPS
        if pure_action == DM.ACTION.CANCEL_GPS:
            self._handle_cancel_gps_action(intent)
            return Service.START_STICKY
        # Skip GPS target
        elif pure_action == DM.ACTION.SKIP_GPS_TARGET:
            self._handle_skip_gps_target_action(intent)
            return Service.START_STICKY
        
        # Handle task-related actions (these need task_id)
        task_id = self._get_task_id(intent, pure_action)
        if not task_id:
            logger.error(f"Error getting task_id from action: {pure_action}")
            return Service.START_STICKY

        # Cancel all Task notifications
        self.notification_manager.cancel_task_notifications()
        # Snooze
        if pure_action == DM.ACTION.SNOOZE_A or pure_action == DM.ACTION.SNOOZE_B:
            self._snooze_action(pure_action, task_id)
            return Service.START_STICKY
        # Cancel and open app
        elif pure_action == DM.ACTION.CANCEL:
            self._cancel_action(pure_action, task_id)
            return Service.START_STICKY
    
    def _handle_app_action(self, intent: Any, pure_action: str) -> int:
        """
        Handles App actions (coming from App)
        - Tasks: update tasks
        - Alarm: stop alarm
        - Notifications: remove task notifications
        - GPS: get location once, start location monitoring, stop location monitoring
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
        
        # GPS actions
        elif pure_action == DM.ACTION.GET_LOCATION_ONCE:
            self._get_location_once_action()
        
        elif pure_action == DM.ACTION.START_LOCATION_MONITORING:
            self._start_location_monitoring_action(intent)
        
        elif pure_action == DM.ACTION.STOP_LOCATION_MONITORING:
            self._stop_location_monitoring_action()

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
        Falls back to current task's ID only for task-related service actions.
        """
        task_id = intent.getStringExtra("task_id")        
        if task_id:
            return task_id
        
        # Fallback to current Task's ID only for task-related actions
        if action and action in [DM.ACTION.SNOOZE_A, DM.ACTION.SNOOZE_B, DM.ACTION.CANCEL]:
            if self.expiry_manager.current_task:
                logger.error(f"Error getting task_id from intent - using current task_id: {self.expiry_manager.current_task.task_id}")
                return self.expiry_manager.current_task.task_id
            if self.expiry_manager.expired_task:
                logger.error(f"Error getting task_id from intent - using expired task_id: {self.expiry_manager.expired_task.task_id}")
                return self.expiry_manager.expired_task.task_id
        
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
        self.notification_manager.cancel_task_notifications()
    
    def _get_location_once_action(self) -> None:
        """Handles request for one-time location from app."""
        try:
            logger.info("Service: Processing location request from app")
            location = self.gps_manager.get_location_once()
            
            if location:
                lat, lon = location
                self._send_location_response(True, lat, lon)
                logger.info(f"Service: Sent location response: {lat}, {lon}")
            else:
                self._send_location_response(False)
                logger.warning("Service: Could not get location, sent failure response")
        except Exception as e:
            logger.error(f"Service: Error handling location request: {e}")
            self._send_location_response(False)
    
    def _start_location_monitoring_action(self, intent: Any) -> None:
        """Handles request to start location monitoring."""
        try:
            # Extract target coordinates from intent
            target_lat_str = intent.getStringExtra("target_lat")
            target_lon_str = intent.getStringExtra("target_lon")
            alert_distance_str = intent.getStringExtra("alert_distance")
            
            if not target_lat_str or not target_lon_str:
                logger.error("Service: Missing target coordinates for location monitoring")
                return
            
            target_lat = float(target_lat_str)
            target_lon = float(target_lon_str)
            alert_distance = float(alert_distance_str) if alert_distance_str else None
            
            logger.info(f"Service: Starting location monitoring for {target_lat}, {target_lon}")
            success = self.gps_manager.start_location_monitoring(target_lat, target_lon, alert_distance)
            
            if success:
                logger.info("Service: Location monitoring started successfully")
            else:
                logger.error("Service: Failed to start location monitoring")
                
        except Exception as e:
            logger.error(f"Service: Error starting location monitoring: {e}")
    
    def _stop_location_monitoring_action(self) -> None:
        """Handles request to stop location monitoring."""
        try:
            logger.info("Service: Stopping location monitoring")
            self.gps_manager.stop_location_monitoring()
            self.audio_manager.audio_player.stop()
        except Exception as e:
            logger.error(f"Service: Error stopping location monitoring: {e}")
    
    def _send_location_response(self, success: bool, lat: float = None, lon: float = None) -> None:
        """Sends location response back to app."""
        try:
            if not self.context:
                logger.error("Service: No context available for location response")
                return
            
            intent = Intent()
            intent.setAction(f"{self.package_name}.{DM.ACTION.LOCATION_RESPONSE}")
            intent.setPackage(self.package_name)
            intent.putExtra(DM.ACTION_TARGET.TARGET, AndroidString(DM.ACTION_TARGET.APP))
            
            if success and lat is not None and lon is not None:
                intent.putExtra("success", AndroidString("true"))
                intent.putExtra("latitude", AndroidString(str(lat)))
                intent.putExtra("longitude", AndroidString(str(lon)))
            else:
                intent.putExtra("success", AndroidString("false"))
            
            self.context.sendBroadcast(intent)
            logger.debug(f"Service: Sent location response, success: {success}")
            
        except Exception as e:
            logger.error(f"Service: Error sending location response: {e}")
    
    def _get_pure_action(self, intent: Any) -> str | None:
        """Extracts and returns the pure action from the intent, or None."""
        action = intent.getAction()
        if not action:
            return None
        
        pure_action = action.split(".")[-1]
        return pure_action

    def _handle_cancel_gps_action(self, intent: Any) -> None:
        """Handles GPS tracking cancellation."""
        try:
            target_id = intent.getStringExtra("target_id")
            logger.info(f"Handling GPS cancel action for target: {target_id}")
            self.service_manager.gps_manager.stop_location_monitoring()
            
        except Exception as e:
            logger.error(f"Error handling cancel GPS action: {e}")

    def _handle_skip_gps_target_action(self, intent: Any) -> None:
        """
        Handles skipping to next GPS target.
        Currently not implemented.
        """
        try:
            target_id = intent.getStringExtra("target_id")
            logger.info(f"Handling skip GPS target action for: {target_id}")
            
            # TODO: Implement multi-target logic
            self.service_manager.gps_manager.stop_location_monitoring()
            
        except Exception as e:
            logger.error(f"Error handling skip GPS target action: {e}")
