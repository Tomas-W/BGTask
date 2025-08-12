import time

from jnius import autoclass  # type: ignore
from typing import Any

from service.service_audio_manager import ServiceAudioManager
from service.service_expiry_manager import ServiceExpiryManager
from service.service_notification_manager import ServiceNotificationManager
from service.service_communication_manager import ServiceCommunicationManager
from service.service_gps_manager import ServiceGpsManager
from managers.tasks.task import Task

from service.service_utils import get_service_timestamp
from managers.device.device_manager import DM

from src.utils.logger import logger

Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")
RunningAppProcessInfo = autoclass("android.app.ActivityManager$RunningAppProcessInfo")
Service = autoclass("android.app.Service")


class ServiceManager:

    LOOP_INTERVAL = 10                       # = 10 seconds
    SERVICE_HEARTBEAT_TICK = 6               # = 60 seconds
    FORCE_FOREGROUND_NOTIFICATION_TICK = 6   # = 60 seconds
    LOOP_SYNC_TICK = 360                     # = 1 hour
    EXPIRY_LOG_TICK = 3                      # = 30 seconds

    MAX_LOOP_DEVIATION = 4                   # = 4 seconds

    """
    Manages the Android background service and Task monitoring, it:
    - Monitors the current Task for expiration
    - Sends notification and triggers alarm when Task is expired
    - Handles Task actions (snooze, cancel) from notifications
    - Updates foreground and Task notifications
    - Writes timestamp to flag file periodically
    """
    def __init__(self):
        self.audio_manager: ServiceAudioManager = ServiceAudioManager()
        self.expiry_manager: ServiceExpiryManager = ServiceExpiryManager(self.audio_manager)
        self.notification_manager: ServiceNotificationManager = ServiceNotificationManager(PythonService.mService,
                                                                                           self.expiry_manager)
        self.gps_manager: ServiceGpsManager = ServiceGpsManager(service_manager=self)

        self.communication_manager = ServiceCommunicationManager(
            service_manager=self,
            audio_manager=self.audio_manager,
            expiry_manager=self.expiry_manager,
            notification_manager=self.notification_manager,
            gps_manager=self.gps_manager
        )
        
        # Loop variables
        self._running: bool = True
        self._in_foreground: bool = False

        # ActivityManager
        self._package_name: str | None = None
        self._activity_manager: Any | None = None
        self._init_activity_manager()

        # Ticks
        self.loop_sync_tick: int = 0
        self.heartbeat_tick: int = 0
        self.foreground_notification_tick: int = 0
        self.expiry_log_tick: int = 0

        # Loop timing
        self._last_loop_time: float = 0
        self._loop_synchronized: bool = False
    
    def run_service(self) -> None:
        """
        Main service loop. Inactive when app is in foreground.
        - Flags service as running
        - Ensures loop is in sync with Task expiry
        - Ensures foreground notification is always active
        - Checks Task expiry
        """
        logger.debug("Starting main service loop")
        
        # Make sure service context is ready
        time.sleep(0.3)

        # Initial checks
        self._flag_service_as_running()
        self.check_task_expiry()
        self.update_foreground_notification_info()

        # GPS check
        self.gps_manager.start_location_monitoring()  # Will skip if no GPS data found


        # Sync loop
        self.synchronize_loop_start()

        while self._running:

            self._update_loop_ticks()
            self._update_loop_time()

            try:
                # ############### ALWAYS RUNS ###############
                self.flag_service_as_running()                   # 60 seconds

                self.synchronize_loop_cycle()                    # 1 hour

                self.force_foreground_notification()             # 60 seconds

                # ############### RUNS IN FOREGROUND ########
                if self.is_app_in_foreground():
                    self._in_foreground = True
                    time.sleep(self.get_loop_interval())
                    continue
                

                # ############### RUNS IN BACKGROUND ########
                else:
                    self.log_expiry_tasks()                      # 30 seconds

                    if self.expiry_manager.current_task is not None:
                        self.check_task_expiry()                 # 10 seconds

                    self._in_foreground = False
                
                time.sleep(self.get_loop_interval())
                
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                time.sleep(self.get_loop_interval())
        
        self.audio_manager.stop_alarm()
    
    def _update_loop_ticks(self) -> None:
        """Updates all loop ticks."""
        self.loop_sync_tick += 1
        self.heartbeat_tick += 1
        self.foreground_notification_tick += 1
        self.expiry_log_tick += 1

    def _update_loop_time(self) -> None:
        """Updates the loop time."""
        self._last_loop_time = time.time()
    
    def cancel_alarm_and_notifications(self) -> None:
        """Cancels the alarm and notifications."""
        logger.trace("Cancelling alarm and notifications")
        self.audio_manager.stop_alarm()
        self.notification_manager.cancel_task_notifications()
    
    def synchronize_loop_start(self) -> None:
        """
        Syncs loop to start at a 10-second interval (01, 11, 21, 31, 41, 51 seconds).
        Synchronizes by sleeping until the next interval.
        """
        current_seconds = time.localtime().tm_sec
        seconds_to_wait = ((current_seconds + 9) // 10 * 10 + 1) - current_seconds
        
        if seconds_to_wait > 1:
            logger.debug(f"Synchronizing loop start: waiting {seconds_to_wait} seconds")
            time.sleep(seconds_to_wait)
        
        self._loop_synchronized = True
    
    def synchronize_loop_cycle(self) -> None:
        """
        Syncs loop to be at a 10-second interval (01, 11, 21, 31, 41, 51 seconds).
        If loop is off by more than LOOP_DEVIATION seconds, resynchronize.
        Synchronizes by sleeping until the next interval.
        """
        if self.loop_sync_tick >= ServiceManager.LOOP_SYNC_TICK:
            logger.debug("Synchronizing loop cycle")
            self.loop_sync_tick = 0
            current_seconds = time.localtime().tm_sec
            seconds_from_boundary = current_seconds % 10
            
            if seconds_from_boundary > ServiceManager.MAX_LOOP_DEVIATION:
                seconds_to_wait = ((current_seconds + 9) // 10 * 10 + 1) - current_seconds
                logger.debug(f"Loop drift detected: {seconds_from_boundary}s from boundary. "
                            f"Resynchronizing: waiting {seconds_to_wait} seconds")
                
                time.sleep(seconds_to_wait)
                logger.debug("Loop resynchronization complete")
    
    def get_loop_interval(self) -> float:
        """
        Returns the time to sleep if loop took less than LOOP_INTERVAL seconds,
         else returns 0.
        """
        now = time.time()
        loop_time = now - self._last_loop_time
        sleep_time = ServiceManager.LOOP_INTERVAL - loop_time

        if sleep_time < 0:
            logger.error(f"Loop took longer than LOOP_INTERVAL ({ServiceManager.LOOP_INTERVAL}) seconds")
            return 0.0

        return sleep_time
    
    def flag_service_as_running(self) -> None:
        """
        Flags service as running if it has been running for SERVICE_HEARTBEAT_TICK seconds.
        """
        if self.heartbeat_tick >= ServiceManager.SERVICE_HEARTBEAT_TICK:
            self.heartbeat_tick = 0
            self._flag_service_as_running()
    
    def _flag_service_as_running(self) -> None:
        """Writes current timestamp to heartbeat flag file."""
        try:
            # Write current timestamp
            with open(DM.PATH.SERVICE_HEARTBEAT_FLAG, "w") as f:
                f.write(str(int(time.time())))
            logger.trace("Service heartbeat flag written")
        
        except Exception as e:
            print(f"Error writing service heartbeat: {e}")

    def force_foreground_notification(self) -> None:
        """
        Forces foreground notification if service has been running for FORCE_FOREGROUND_NOTIFICATION_TICK seconds.
        """
        if self.foreground_notification_tick >= ServiceManager.FORCE_FOREGROUND_NOTIFICATION_TICK:
            self.foreground_notification_tick = 0
            self._force_foreground_notification()

    def _force_foreground_notification(self) -> None:
        """
        Displays foreground notification with current Task info.
        If no Task is active, displays "No tasks to monitor" message.
        """
        if self.notification_manager and self.notification_manager._has_foreground_notification():
            return
        
        if self.expiry_manager.current_task:
            time_label = get_service_timestamp(self.expiry_manager.current_task)
            message = self.expiry_manager.current_task.message
            with_buttons = True
        else:
            time_label = "No tasks to monitor"
            message = ""
            with_buttons = False
            
        self.notification_manager.ensure_foreground_notification(
            time_label,
            message,
            with_buttons
        )
    
    def update_foreground_notification_info(self) -> None:
        """Updates the foreground notification with the current Task's info."""
        if self.expiry_manager.current_task:
            time_label = get_service_timestamp(self.expiry_manager.current_task)
            message = self.expiry_manager.current_task.message

            self.notification_manager.show_foreground_notification(
                time_label,
                message,
                with_buttons=True
            )
        
        else:
            time_label = "No tasks to monitor"
            message = ""
            
            self.notification_manager.show_foreground_notification(
                time_label,
                message,
                with_buttons=False
            )
    
    def is_app_in_foreground(self) -> bool:
        """Returns True if App is running in the foreground."""
        try:
            if not self._activity_manager or not self._package_name:
                return False
                
            # Get running app processes
            running_apps = self._activity_manager.getRunningAppProcesses()
            if not running_apps:
                return False
                
            # Check if our app is in foreground
            for process in running_apps:
                if (process.processName == self._package_name and 
                    process.importance == RunningAppProcessInfo.IMPORTANCE_FOREGROUND):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking app state: {e}")
            return False
    
    def check_task_expiry(self) -> None:
        """Returns True if the current Task is expired"""
        if not self.expiry_manager.is_task_expired():
            return
        
        logger.trace(f"Task expired, handling expiry")
        self._handle_task_expiry()
    
    def _handle_task_expiry(self) -> None:
        """Handles the expiry of a Task."""
        if self.expiry_manager.expired_task:
            self.expiry_manager.expired_task.expired = True
            self.expiry_manager._save_task_changes(
                self.expiry_manager.expired_task.task_id, 
                {"expired": True}
            )
        
        self.notification_manager.cancel_task_notifications()

        expired_task = self.expiry_manager.handle_task_expired()
        if expired_task:
            self.notify_user_of_expiry(expired_task)
    
    def log_expiry_tasks(self) -> None:
        """Logs the current and expired Tasks."""
        if self.expiry_log_tick >= ServiceManager.EXPIRY_LOG_TICK:
            self.expiry_log_tick = 0
            self.expiry_manager._log_expiry_tasks()
    
    def notify_user_of_expiry(self, expired_task: Task) -> None:
        """
        Notifies the user of the expiry of a Task by:
        - Showing a notification
        - Playing an alarm
        """
        self.notification_manager.show_task_notification(
                    "Task Expired",
                    expired_task.message
                )
        self.audio_manager.trigger_alarm(expired_task)
        self.update_foreground_notification_info()
        logger.trace(f"Showed and updated notifications")
    
    def _init_activity_manager(self) -> None:
        """Initializes ActivityManager and gets package name."""
        try:
            context = PythonService.mService.getApplicationContext()
            self._activity_manager = context.getSystemService(Context.ACTIVITY_SERVICE)
            self._package_name = context.getPackageName()
                
        except Exception as e:
            logger.error(f"Error initializing ActivityManager: {e}")
