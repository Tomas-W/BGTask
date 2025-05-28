import time
import os

from datetime import timedelta

from jnius import autoclass  # type: ignore
from typing import TYPE_CHECKING

from managers.tasks.task_manager_utils import Task
from src.managers.settings_manager import SettingsManager

from service.service_audio_manager import ServiceAudioManager
from service.service_expiry_manager import ServiceExpiryManager
from service.service_utils import get_service_timestamp
from service.service_device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from service.service_notification_manager import ServiceNotificationManager

Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")
RunningAppProcessInfo = autoclass("android.app.ActivityManager$RunningAppProcessInfo")
Service = autoclass("android.app.Service")


LOOP_INTERVAL = 10                       # = 10 seconds
SERVICE_HEARTBEAT_TICK = 6               # = 60 seconds
FORCE_FOREGROUND_NOTIFICATION_TICK = 6   # = 60 seconds
LOOP_SYNC_TICK = 360                     # = 1 hour

MAX_LOOP_DEVIATION = 4                   # = 4 seconds


class ServiceManager:
    """
    Manages the Android background service and Task monitoring, it:
    - Monitors the current Task for expiration
    - Sends notification and triggers alarm when Task is expired
    - Handles Task actions (snooze, cancel) from notifications
    - Updates foreground and Task notifications
    - Writes timestamp to flag file periodically
    """
    def __init__(self):
        self.notification_manager: "ServiceNotificationManager | None" = None  # Initialized in service loop
        self.audio_manager: ServiceAudioManager = ServiceAudioManager()
        self.expiry_manager: ServiceExpiryManager = ServiceExpiryManager(self.audio_manager)
        self.settings_manager = None

        # Loop variables
        self._running: bool = True
        self._need_foreground_notification_update: bool = True
        self._in_foreground: bool = False

        # ActivityManager
        self._app_package_name = None
        self._activity_manager = None
        self._init_activity_manager()

        # Ticks
        self.loop_sync_tick = 0
        self.heartbeat_tick = 0
        self.foreground_notification_tick = 0

        # Loop timing
        self._last_loop_time = 0
        self._loop_interval = LOOP_INTERVAL
        self._loop_synchronized = False
    
    def run_service(self) -> None:
        """
        Main service loop.
        - Ensures loop is in sync with Task expiry
        - Ensures foreground notification is always active
        - Updates Tasks when app's on_pause has set a flag file
        - Checks for foreground notification updates
        - Checks if the Task is expired
        - If the Task is expired, show notification and get next Task
        """
        logger.debug("Starting main service loop")
        
        # Make sure service context is ready
        time.sleep(0.3)

        # Set up loop
        self._init_settings_manager()
        self.flag_service_as_running()

        self.check_task_expiry()
        self.update_foreground_notification_info()

        self.synchronize_loop_start()

        while self._running:
            self.loop_sync_tick += 1
            self.heartbeat_tick += 1
            self.foreground_notification_tick += 1

            self._last_loop_time = time.time()

            logger.trace(f"Loop tick")

            try:
                # ############### ALWAYS RUNS ###############
                self.synchronize_loop_cycle()                    # 1 hour

                self.flag_service_as_running()                   # 60 seconds

                self.force_foreground_notification()             # 60 seconds
                
                if self._need_foreground_notification_update:
                    self.update_foreground_notification_info()   # 10 seconds
                

                # ############### RUNS IN FOREGROUND ###############
                if self.is_app_in_foreground():
                    logger.debug("App is in foreground")

                    # if not self._in_foreground:
                    #     self.cancel_alarm_and_notifications()                  # Once per foregrounded
                    #     self._in_foreground = True
                    #     logger.critical("Canceled SERVICE ALARM because _in_foreground was False")
                    
                    self._in_foreground = True
                    # time.sleep(0.5)
                    time.sleep(self.get_loop_interval())
                    # Dont run Task checks in foreground
                    continue
                

                # ############### RUNS IN BACKGROUND ###############
                else:
                    logger.debug("App is in background")

                    if self.expiry_manager.current_task is not None:
                        self.check_task_expiry()                     # 10 seconds

                    self._in_foreground = False
                
                time.sleep(self.get_loop_interval())
                
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                time.sleep(self.get_loop_interval())
        
        self.audio_manager.stop_alarm()
    
    def cancel_alarm_and_notifications(self) -> None:
        """Cancels the alarm and notifications."""
        self.audio_manager.stop_alarm()
        logger.debug("Stopped alarm and vibrations")

        self.notification_manager.cancel_all_notifications()
        logger.debug("Cancelled all notifications")
        
    def synchronize_loop_start(self) -> None:
        """'
        Sync loop to start at a 10-second interval (01, 11, 21, 31, 41, 51 seconds).
        Synchronizes by sleeping until the next interval.
        """
        current_seconds = time.localtime().tm_sec
        seconds_to_wait = ((current_seconds + 9) // 10 * 10 + 1) - current_seconds
        
        if seconds_to_wait > 0:
            logger.debug(f"Synchronizing loop start: waiting {seconds_to_wait} seconds")
            time.sleep(seconds_to_wait)
        
        self._loop_synchronized = True
        logger.debug("Loop synchronization complete")
    
    def synchronize_loop_cycle(self) -> None:
        """
        Sync loop to be at a 10-second interval (01, 11, 21, 31, 41, 51 seconds).
        If loop is off by more than LOOP_DEVIATION seconds, resynchronize.
        Synchronizes by sleeping until the next interval.
        """
        if self.loop_sync_tick >= LOOP_SYNC_TICK:
            self.loop_sync_tick = 0
            current_seconds = time.localtime().tm_sec
            seconds_from_boundary = current_seconds % 10
            
            if seconds_from_boundary > MAX_LOOP_DEVIATION:
                seconds_to_wait = ((current_seconds + 9) // 10 * 10 + 1) - current_seconds
                logger.debug(f"Loop drift detected: {seconds_from_boundary}s from boundary. "
                            f"Resynchronizing: waiting {seconds_to_wait} seconds")
                
                time.sleep(seconds_to_wait)
                logger.debug("Loop resynchronization complete")
    
    def get_loop_interval(self) -> None:
        """
        If loop took less than LOOP_INTERVAL seconds, return the difference,
         else return 0.
        """
        now = time.time()
        loop_time = now - self._last_loop_time
        sleep_time = self._loop_interval - loop_time

        if sleep_time < 0:
            logger.error(f"Loop took longer than LOOP_INTERVAL ({self._loop_interval}) seconds")
            return 0

        return sleep_time
    
    def flag_service_as_running(self) -> None:
        """
        If service has been running for SERVICE_HEARTBEAT_TICK seconds,
         flag it as running.
        """
        if self.heartbeat_tick >= SERVICE_HEARTBEAT_TICK:
            self.heartbeat_tick = 0
            self._flag_service_as_running()
    
    def _flag_service_as_running(self) -> None:
        """Writes current timestamp to a file."""
        try:
            # Write current timestamp
            with open(DM.PATH.SERVICE_HEARTBEAT_FLAG, "w") as f:
                f.write(str(int(time.time())))
            logger.debug("Service heartbeat flag written")
        
        except Exception as e:
            print(f"Error writing service heartbeat: {e}")

    def force_foreground_notification(self) -> None:
        """
        If service has been running for FORCE_FOREGROUND_NOTIFICATION_TICK seconds,
         check if the foreground notification needs to be re-displayed.
        """
        if self.foreground_notification_tick >= FORCE_FOREGROUND_NOTIFICATION_TICK:
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
        logger.debug("Updating foreground notification info")
        if self.expiry_manager.current_task:
            time_label = get_service_timestamp(self.expiry_manager.current_task)
            message = self.expiry_manager.current_task.message
            self.notification_manager.show_foreground_notification(
                time_label,
                message,
                with_buttons=True
            )
        
        else:
            self.notification_manager.show_foreground_notification(
                "No tasks to monitor",
                "",
                with_buttons=False
            )
        
        self._need_foreground_notification_update = False
    
    def is_app_in_foreground(self) -> bool:
        """Check if app is running in the foreground."""
        try:
            if not self._activity_manager or not self._app_package_name:
                return False
                
            # Get running app processes
            running_apps = self._activity_manager.getRunningAppProcesses()
            if not running_apps:
                return False
                
            # Check if our app is in foreground
            for process in running_apps:
                if (process.processName == self._app_package_name and 
                    process.importance == RunningAppProcessInfo.IMPORTANCE_FOREGROUND):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking app state: {e}")
            return False
    
    def check_task_expiry(self) -> bool:
        """Returns True if the current Task is expired"""
        logger.debug(f"Current task: {DM.get_task_log(self.expiry_manager.current_task) if self.expiry_manager.current_task else None}")
        logger.debug(f"Expired task: {DM.get_task_log(self.expiry_manager.expired_task) if self.expiry_manager.expired_task else None}")
        logger.debug("Active tasks:")

        for task in self.expiry_manager.active_tasks:
            logger.debug(f"      {DM.get_task_log(task)}")
            
        if self.expiry_manager.is_task_expired():
            logger.debug("Task expired, showing notification")

            if self.expiry_manager.expired_task:
                # self.clean_up_previous_task()
                self.notification_manager.cancel_all_notifications()

            expired_task = self.expiry_manager.handle_task_expired()
            if expired_task:
                self.notify_user_of_expiry(expired_task)
    
    def clean_up_previous_task(self) -> None:
        """Cleans up the previous Task's alarm and notifications"""
        self.notification_manager.cancel_all_notifications()
        # self.expiry_manager.clear_expired_task()
        logger.debug("Cleaned up previous expired task")
    
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
    
    def handle_action(self, action: str) -> int:
        """
        Handles notification button actions from foreground or Task notifications.
        Always returns START_STICKY to ensure the service keeps running.
        """
        # Rework logic becasue of app communication
        # if not self.expiry_manager.current_task and not self.expiry_manager.expired_task:
        #     logger.debug("No current task to handle action for")
        #     return Service.START_STICKY
        # ############### SERVICE ACTIONS ###############
        # Cancel all notifications
        if self.notification_manager:
            self.notification_manager.cancel_all_notifications()
        
        # Clicked Snooze A button
        if action.endswith(DM.ACTION.SNOOZE_A):
            self.expiry_manager.snooze_task(action)
            self.audio_manager.stop_alarm()
            self._need_foreground_notification_update = True
            # Add immediate updates
            self.update_foreground_notification_info()
            return Service.START_REDELIVER_INTENT

        # Clicked Snooze B button
        if action.endswith(DM.ACTION.SNOOZE_B):
            self.expiry_manager.snooze_task(action)
            self.audio_manager.stop_alarm()
            self._need_foreground_notification_update = True
            # Add immediate updates
            self.update_foreground_notification_info()
            return Service.START_REDELIVER_INTENT
        
        # Clicked Cancel button or swiped notification
        elif action.endswith(DM.ACTION.CANCEL):
            if self.expiry_manager.expired_task:
                task_id = self.expiry_manager.expired_task.task_id
                if self.settings_manager:
                    self.settings_manager.set_cancelled_task_id(task_id)
                else:
                    logger.error("Settings manager not initialized, cannot store cancelled task ID")
            
            self.expiry_manager.cancel_task()
            self._need_foreground_notification_update = True
            self.audio_manager.stop_alarm()
            # Add immediate updates
            self.update_foreground_notification_info()
            return Service.START_STICKY
        
        # Clicked notification to open app
        elif action.endswith(DM.ACTION.OPEN_APP):
            if self.expiry_manager.expired_task:
                task_id = self.expiry_manager.expired_task.task_id
                logger.debug(f"Storing cancelled task ID: {task_id}")
                
                if self.settings_manager:
                    # Notify app to stop alarm and show popup
                    self.settings_manager.set_cancelled_task_id(task_id)
                else:
                    logger.error("Settings manager not initialized, cannot store cancelled task ID")
            
            self.expiry_manager.cancel_task()
            self._need_foreground_notification_update = True
            self.audio_manager.stop_alarm()
            # Add immediate updates
            self.update_foreground_notification_info()
            self._open_app()
        
        # ############### APP ACTIONS ###############
        # Stop alarm when app is opened manually
        elif action.endswith(DM.ACTION.STOP_ALARM):
            logger.debug("STOPPING ALARM WITH ACTION")
            self.audio_manager.stop_alarm()
            self.update_foreground_notification_info()
            logger.debug("STOPPED ALARM WITH ACTION")
            return Service.START_STICKY
        
        # Update Serice Tasks after App has updated them
        elif action.endswith(DM.ACTION.UPDATE_TASKS):
            self.expiry_manager._refresh_tasks()
            self.update_foreground_notification_info()
            logger.debug("REFRESHED TASKS WITH ACTION")
            return Service.START_STICKY
        
        else:
            logger.error(f"Unknown action: {action}")
            self.audio_manager.stop_alarm()
            return Service.START_STICKY

    def _open_app(self) -> None:
        """Opens the app from Task notification"""
        try:
            context = self.notification_manager.context
            intent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName())
            if intent:
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                intent.addCategory("android.intent.category.LAUNCHER")
                context.startActivity(intent)
                logger.debug("Launched app activity")
        
        except Exception as e:
            logger.error(f"Error launching app: {e}")
    
    def _init_notification_manager(self) -> None:
        """Initialize the NotificationManager"""
        if self.notification_manager is None:
            from service.service_notification_manager import ServiceNotificationManager  # type: ignore
            self.notification_manager = ServiceNotificationManager(PythonService.mService)
    
    def _init_settings_manager(self) -> None:
        """Initialize the SettingsManager with retries"""
        if self.settings_manager is None:
            try:
                # reties to guarantee context
                self.settings_manager = SettingsManager(max_retries=3, retry_delay=0.2)
                logger.debug("Successfully initialized SettingsManager")
            except Exception as e:
                logger.error(f"Error initializing SettingsManager after retries: {e}")
                # Keep service running

    def _init_activity_manager(self) -> None:
        """Initialize ActivityManager and get package name"""
        try:
            context = PythonService.mService.getApplicationContext()
            self._activity_manager = context.getSystemService(Context.ACTIVITY_SERVICE)
            self._app_package_name = context.getPackageName()
            logger.debug("Initialized ActivityManager")
        
        except Exception as e:
            logger.error(f"Error initializing ActivityManager: {e}")
