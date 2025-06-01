# service/main.py
from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore
from typing import Any

from service.service_manager import ServiceManager
from service.service_device_manager import DM

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

# Global ServiceManager
service_manager: ServiceManager | None = None
# Global BroadcastReceiver
receiver: BroadcastReceiver | None = None
# Global wake lock
wake_lock: Any | None = None

def on_receive_callback(service_manager: ServiceManager, context: Any, intent: Any) -> None:
    """Callback for handling received broadcast actions"""
    try:
        action = intent.getAction()
        if action:
            pure_action = action.split(".")[-1]
            if pure_action == "BOOT_COMPLETED":
                # Start service on boot
                start_service()
            else:
                service_manager.handle_action(pure_action, intent)
    
    except Exception as e:
        logger.error(f"Error in broadcast receiver: {e}")

def create_broadcast_receiver(service_manager: ServiceManager) -> BroadcastReceiver | None:
    """
    Creates a BroadcastReceiver for handling notification actions.
    Actions:
    - Snooze A
    - Snooze B
    - Cancel
    - Open App
    - Boot completed
    - Service restart
    Snooze A & Snooze B are loaded from user settings.
    """
    try:
        context = PythonService.mService.getApplicationContext()
        if not context:
            logger.error("Failed to get application context: PythonService.mService is None")
            return None
            
        package_name = context.getPackageName()
        if not package_name:
            logger.error("Failed to get package name")
            return None
        
        # Register actions to receiver
        actions = _get_broadcast_actions(package_name)
        # Add boot completed action
        actions.append("android.intent.action.BOOT_COMPLETED")
        
        # Create receiver with the standalone callback
        receiver = BroadcastReceiver(
            lambda ctx, intent: on_receive_callback(service_manager, ctx, intent),
            actions
        )
        return receiver
    
    except Exception as e:
        logger.error(f"Error creating broadcast receiver: {e}")
        return None

def _get_broadcast_actions(package_name: str) -> list[str]:
    """Get list of broadcast actions"""
    return [
        f"{package_name}.{DM.ACTION.SNOOZE_A}",
        f"{package_name}.{DM.ACTION.SNOOZE_B}",
        f"{package_name}.{DM.ACTION.CANCEL}",
        f"{package_name}.{DM.ACTION.OPEN_APP}",
        # f"{package_name}.{DM.ACTION.STOP_ALARM}",
        # f"{package_name}.{DM.ACTION.UPDATE_TASKS}",
        f"{package_name}.{DM.ACTION.RESTART_SERVICE}"  # Action for service restart
    ]

def start_broadcast_receiver(receiver: Any) -> None:
    """Starts the BroadcastReceiver"""
    try:
        receiver.start()
        logger.trace("Started BroadcastReceiver")
    
    except Exception as e:
        logger.error(f"Error starting BroadcastReceiver: {e}")

def schedule_service_restart() -> None:
    """Schedule a service restart using AlarmManager with exponential backoff"""
    try:
        context = PythonService.mService.getApplicationContext()
        if not context:
            logger.error("Failed to get application context for service restart")
            return

        # Create intent for service restart
        intent = Intent(context, PythonService.mService.getClass())
        intent.setAction(f"{context.getPackageName()}.{DM.ACTION.RESTART_SERVICE}")
        
        # Create pending intent with proper flags
        flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_ONE_SHOT
        if BuildVersion.SDK_INT >= 31:  # Android 12 or higher
            flags |= PendingIntent.FLAG_IMMUTABLE
        pending_intent = PendingIntent.getService(
            context, 
            0, 
            intent, 
            flags
        )

        # Get alarm manager
        alarm_manager = context.getSystemService(Context.ALARM_SERVICE)
        if not alarm_manager:
            logger.error("Failed to get AlarmManager")
            return

        # Calculate retry delay with exponential backoff
        if not hasattr(schedule_service_restart, "retry_count"):
            schedule_service_restart.retry_count = 0
        schedule_service_restart.retry_count += 1
        
        # Max delay of 5 minutes
        delay = min(300000, 1000 * (2 ** schedule_service_restart.retry_count))
        
        # Schedule restart with exact timing based on Android version
        trigger_time = SystemClock.elapsedRealtime() + delay
        
        if BuildVersion.SDK_INT >= 31:  # Android 12 or higher
            # Use setExactAndAllowWhileIdle for maximum reliability
            alarm_manager.setExactAndAllowWhileIdle(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                trigger_time,
                pending_intent
            )
        elif BuildVersion.SDK_INT >= 23:  # Android 6.0 or higher
            # Use setAlarmClock as fallback
            alarm_manager.setAlarmClock(
                AlarmManager.AlarmClockInfo(trigger_time, pending_intent),
                pending_intent
            )
        else:
            # Use setExact for older versions
            alarm_manager.setExact(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                trigger_time,
                pending_intent
            )
        logger.debug(f"Scheduled service restart with {delay}ms delay")

    except Exception as e:
        logger.error(f"Error scheduling service restart: {e}")
        # Attempt immediate restart as fallback
        try:
            start_service()
        except Exception as e2:
            logger.error(f"Error in fallback service restart: {e2}")

def acquire_wake_lock() -> None:
    """Acquire a wake lock to keep the service running"""
    global wake_lock
    try:
        context = PythonService.mService.getApplicationContext()
        if not context:
            logger.error("Failed to get application context for wake lock")
            return

        power_manager = context.getSystemService(Context.POWER_SERVICE)
        if not power_manager:
            logger.error("Failed to get PowerManager")
            return

        # Release existing wake lock if any
        release_wake_lock()

        # Create wake lock with proper flags for maximum reliability
        wake_lock = power_manager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK | 
            PowerManager.ON_AFTER_RELEASE,
            "BGTask::ServiceWakeLock"
        )
        
        # Set a timeout that will auto-renew
        wake_lock.acquire(6 * 60 * 60 * 1000)  # 6 hours timeout
        
        # Schedule wake lock renewal using a Handler on the main thread
        Looper = autoclass("android.os.Looper")
        Handler = autoclass("android.os.Handler")
        
        # Prepare looper for the current thread if needed
        if Looper.myLooper() is None:
            Looper.prepare()
        
        handler = Handler(Looper.getMainLooper())
        
        def renew_wake_lock():
            try:
                if wake_lock and wake_lock.isHeld():
                    wake_lock.acquire(6 * 60 * 60 * 1000)  # Renew for another 6 hours
                    handler.postDelayed(renew_wake_lock, 5 * 60 * 60 * 1000)  # Schedule next renewal in 5 hours
                    logger.debug("Renewed wake lock")
            except Exception as e:
                logger.error(f"Error renewing wake lock: {e}")
                # Try to reacquire wake lock
                try:
                    acquire_wake_lock()
                except Exception as e2:
                    logger.error(f"Error reacquiring wake lock: {e2}")
        
        # Schedule first renewal in 5 hours
        handler.postDelayed(renew_wake_lock, 5 * 60 * 60 * 1000)
        logger.debug("Acquired wake lock with auto-renewal")

    except Exception as e:
        logger.error(f"Error acquiring wake lock: {e}")
        # Try to recover by scheduling service restart
        schedule_service_restart()

def release_wake_lock() -> None:
    """Release the wake lock if held"""
    global wake_lock
    try:
        if wake_lock:
            if wake_lock.isHeld():
                wake_lock.release()
                logger.debug("Released wake lock")
            wake_lock = None
    except Exception as e:
        logger.error(f"Error releasing wake lock: {e}")
        wake_lock = None  # Ensure it's cleared even on error

def start_service() -> None:
    """Start the service"""
    try:
        context = PythonService.mService.getApplicationContext()
        if not context:
            logger.error("Failed to get application context for service start")
            return

        intent = Intent(context, PythonService.mService.getClass())
        intent.setAction(f"{context.getPackageName()}.{DM.ACTION.RESTART_SERVICE}")
        
        if BuildVersion.SDK_INT >= 26:  # Android 8.0 or higher
            context.startForegroundService(intent)
        else:
            context.startService(intent)
        logger.debug("Started service")

    except Exception as e:
        logger.error(f"Error starting service: {e}")

def on_start_command(intent: Any | None, flags: int, start_id: int) -> int:
    """
    Service onStartCommand callback.
    - Enables auto-restart
    - Initializes ServiceManager
    - Initializes NotificationManager
    - Initializes BroadcastReceiver
    - Starts Service
    - Acquires wake lock
    """
    global service_manager, receiver
    
    try:
        # Reset retry count on successful start
        if hasattr(schedule_service_restart, "retry_count"):
            schedule_service_restart.retry_count = 0

        # Enable auto-restart
        if not PythonService.mService:
            logger.error("PythonService.mService is None")
            return Service.START_STICKY
            
        PythonService.mService.setAutoRestartService(True)

        # Acquire wake lock
        acquire_wake_lock()

        # Initialize ServiceManager
        if service_manager is None:
            service_manager = ServiceManager()
            service_manager._init_notification_manager()
            service_manager._init_settings_manager()
            
            # Create and start broadcast receiver
            receiver = create_broadcast_receiver(service_manager)
            if receiver:
                start_broadcast_receiver(receiver)
            
            # Start service loop
            service_manager.run_service()
        
        return Service.START_STICKY

    except Exception as e:
        logger.error(f"Error in on_start_command: {e}")
        schedule_service_restart()
        return Service.START_STICKY

def on_destroy() -> None:
    """Service onDestroy callback"""
    global service_manager, receiver, wake_lock
    
    try:
        # Release wake lock
        release_wake_lock()
        
        # Stop broadcast receiver
        if receiver:
            try:
                receiver.stop()
            except Exception as e:
                logger.error(f"Error stopping broadcast receiver: {e}")
            receiver = None
        
        # Stop service manager
        if service_manager:
            service_manager._running = False
            service_manager.cancel_alarm_and_notifications()
            service_manager = None
        
        # Schedule service restart
        schedule_service_restart()
        
        logger.debug("Service destroyed")
    
    except Exception as e:
        logger.error(f"Error in on_destroy: {e}")
        schedule_service_restart()

def on_task_removed(root_intent: Any) -> None:
    """Service onTaskRemoved callback"""
    try:
        logger.debug("Service task removed")
        schedule_service_restart()
    
    except Exception as e:
        logger.error(f"Error in on_task_removed: {e}")
        schedule_service_restart()

def main() -> None:
    """Main entry point for the background service"""
    try:
        logger.trace("Starting background service")
        on_start_command(intent=None,
                         flags=0,
                         start_id=1)
    
    except Exception as e:
        logger.error(f"Error in Service main: {e}")
        on_destroy()

if __name__ == "__main__":
    main()
