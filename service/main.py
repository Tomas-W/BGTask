from jnius import autoclass  # type: ignore
from typing import Any, Optional

from service.service_manager import ServiceManager
from managers.device.device_manager import DM
from src.utils.logger import logger

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")
AlarmManager = autoclass("android.app.AlarmManager")
PendingIntent = autoclass("android.app.PendingIntent")
Intent = autoclass("android.content.Intent")
SystemClock = autoclass("android.os.SystemClock")
PowerManager = autoclass("android.os.PowerManager")
Context = autoclass("android.content.Context")
BuildVersion = autoclass("android.os.Build$VERSION")
Looper = autoclass("android.os.Looper")
Handler = autoclass("android.os.Handler")


class BackgroundService:
    """Main background service implementation"""
    
    WAKE_LOCK_TIMEOUT: int = 6 * 60 * 60 * 1000     # 6 hours
    WAKE_LOCK_RENEWAL: int = 5 * 60 * 60 * 1000     # 5 hours
    MAX_RETRY_DELAY: int = 300000                   # 5 minutes
    WAKE_LOCK_TAG: str = "BGTask::ServiceWakeLock"
    
    def __init__(self) -> None:
        self._service_manager: Optional[ServiceManager] = None
        self._wake_lock: Optional[Any] = None
        self._retry_count: int = 0
        self._handler: Optional[Any] = None

    @property
    def context(self) -> Any:
        """Gets and returns the Application context."""
        context = PythonService.mService.getApplicationContext()
        if not context:
            raise RuntimeError("Failed to get Application context")
        
        return context

    def _setup_wake_lock_renewal(self) -> None:
        """Sets up automatic wake lock renewal."""
        if Looper.myLooper() is None:
            Looper.prepare()
        
        self._handler = Handler(Looper.getMainLooper())
        
        def renew_wake_lock() -> None:
            try:
                if self._wake_lock and self._wake_lock.isHeld():
                    # Acquire new wake lock and schedule next renewal
                    self._wake_lock.acquire(BackgroundService.WAKE_LOCK_TIMEOUT)
                    self._handler.postDelayed(
                        renew_wake_lock, 
                        BackgroundService.WAKE_LOCK_RENEWAL
                    )
                    logger.trace("Renewed wake lock")
            
            except Exception as e:
                logger.error(f"Error renewing wake lock: {e}")
                self.acquire_wake_lock()

        # Schedule first renewal
        self._handler.postDelayed(
            renew_wake_lock, 
            BackgroundService.WAKE_LOCK_RENEWAL
        )

    def acquire_wake_lock(self) -> None:
        """Acquires and maintains a wake lock."""
        try:
            # Get Android power manager service
            power_manager = self.context.getSystemService(Context.POWER_SERVICE)
            if not power_manager:
                raise RuntimeError("Failed to get PowerManager")

            self.release_wake_lock()

            # Create new wake lock with partial wake lock flag
            # Keeps CPU running but allows screen to turn off
            self._wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK | PowerManager.ON_AFTER_RELEASE,
                BackgroundService.WAKE_LOCK_TAG
            )
            
            # Acquire wake lock and setup auto-renewal
            self._wake_lock.acquire(BackgroundService.WAKE_LOCK_TIMEOUT)
            self._setup_wake_lock_renewal()
            logger.trace("Acquired wake lock with auto-renewal")

        except Exception as e:
            logger.error(f"Error acquiring wake lock: {e}")
            self.schedule_restart()

    def release_wake_lock(self) -> None:
        """Releases the wake lock."""
        try:
            if self._wake_lock and self._wake_lock.isHeld():
                self._wake_lock.release()
                logger.debug("Released wake lock")
        
        finally:
            self._wake_lock = None

    def schedule_restart(self) -> None:
        """Schedules Service restart with exponential backoff."""
        try:
            intent = Intent(self.context, PythonService.mService.getClass())
            intent.setAction(f"{self.context.getPackageName()}.{DM.ACTION.RESTART_SERVICE}")
            
            # Set flags for pending intent
            flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_ONE_SHOT
            if BuildVersion.SDK_INT >= 31:  # Android 12+
                flags |= PendingIntent.FLAG_IMMUTABLE

            # Create pending intent for restart
            pending_intent = PendingIntent.getService(
                self.context, 0, intent, flags
            )
            # Get alarm manager for scheduling
            alarm_manager = self.context.getSystemService(Context.ALARM_SERVICE)
            if not alarm_manager:
                raise RuntimeError("Failed to get AlarmManager")
            # Calculate delay
            self._retry_count += 1
            delay = min(
                BackgroundService.MAX_RETRY_DELAY, 
                1000 * (2 ** self._retry_count)
            )
            trigger_time = SystemClock.elapsedRealtime() + delay

            # Schedule based on Android version
            self._schedule_alarm(alarm_manager, trigger_time, pending_intent)
            logger.trace(f"Scheduled restart with {delay}ms delay")

        except Exception as e:
            logger.error(f"Error scheduling restart: {e}")
            self._start()
    
    def _schedule_alarm(self, alarm_manager: Any, trigger_time: int, pending_intent: Any) -> None:
        """Schedules the alarm using the appropriate method based on Android version."""
        if BuildVersion.SDK_INT >= 31:    # Android 12+
            alarm_manager.setExactAndAllowWhileIdle(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                trigger_time,
                pending_intent
            )
        elif BuildVersion.SDK_INT >= 23:  # Android 6.0+
            alarm_manager.setAlarmClock(
                AlarmManager.AlarmClockInfo(trigger_time, pending_intent),
                pending_intent
            )
        else:                             # Android 5.0+
            alarm_manager.setExact(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                trigger_time,
                pending_intent
            )

    def _start(self) -> None:
        """Starts the Service."""
        try:
            intent = Intent(self.context, PythonService.mService.getClass())
            intent.setAction(f"{self.context.getPackageName()}.{DM.ACTION.RESTART_SERVICE}")
            
            if BuildVersion.SDK_INT >= 26:  # Android 8.0+
                self.context.startForegroundService(intent)
            else:
                self.context.startService(intent)
            logger.debug("Started background Service")

        except Exception as e:
            logger.error(f"Error starting background Service: {e}")

    def on_start_command(self, intent: Optional[Any], flags: int, start_id: int) -> int:
        """Handles the Service start command."""
        try:
            self._retry_count = 0
            if not PythonService.mService:
                raise RuntimeError("PythonService.mService is None")
            
            # Auto-restart and wake lock
            PythonService.mService.setAutoRestartService(True)
            self.acquire_wake_lock()

            # Initialize and start service manager if needed
            if not self._service_manager:
                self._service_manager = ServiceManager()
                self._service_manager.run_service()
            
            return Service.START_STICKY

        except Exception as e:
            logger.error(f"Error handling start command: {e}")
            self.schedule_restart()
            return Service.START_STICKY

    def on_destroy(self) -> None:
        """Handles Service destruction."""
        try:
            self.release_wake_lock()
            
            # Clean up service manager
            if self._service_manager:
                self._service_manager._running = False
                self._service_manager.cancel_alarm_and_notifications()
                self._service_manager = None
            
            # Schedule restart
            self.schedule_restart()
            logger.debug("Service destroyed")
        
        except Exception as e:
            logger.error(f"Error destroying Service: {e}")
            self.schedule_restart()


# Global service instance
_service: Optional[BackgroundService] = None


def main() -> None:
    """Service entry point."""
    global _service
    try:
        logger.trace("Starting background Service")
        _service = BackgroundService()
        _service.on_start_command(None, 0, 1)
    
    except Exception as e:
        logger.error(f"Error starting Service: {e}")
        if _service:
            _service.on_destroy()


if __name__ == "__main__":
    main()
