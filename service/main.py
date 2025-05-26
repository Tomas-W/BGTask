from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore
from typing import Any

from service.service_manager import ServiceManager
from service.service_device_manager import DM

from src.utils.logger import logger

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")


# Global ServiceManager
service_manager: ServiceManager | None = None
# Global BroadcastReceiver
receiver: BroadcastReceiver | None = None

def on_receive_callback(service_manager: ServiceManager, context: Any, intent: Any) -> None:
    """Callback for handling received broadcast actions"""
    try:
        action = intent.getAction()
        if action:
            pure_action = action.split(".")[-1]
            service_manager.handle_action(pure_action)
    
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
        
        # Create receiver with the standalone callback
        receiver = BroadcastReceiver(
            lambda ctx, intent: on_receive_callback(service_manager, ctx, intent),
            actions=actions
        )
        logger.trace("Created BroadcastReceiver")
        return receiver
        
    except Exception as e:
        logger.error(f"Error setting up BroadcastReceiver: {e}")
        return None


def _get_broadcast_actions(package_name: str) -> list[str]:
    """
    Returns a list of actions for the BroadcastReceiver.
    """
    return [
        f"{package_name}.{DM.ACTION.SNOOZE_A}",
        f"{package_name}.{DM.ACTION.SNOOZE_B}",
        f"{package_name}.{DM.ACTION.CANCEL}",
        f"{package_name}.{DM.ACTION.OPEN_APP}",
        f"{package_name}.{DM.ACTION.STOP_ALARM}"
    ]


def start_broadcast_receiver(receiver: Any) -> None:
    """Starts the BroadcastReceiver"""
    try:
        receiver.start()
        logger.trace("Started BroadcastReceiver")
    
    except Exception as e:
        logger.error(f"Error starting BroadcastReceiver: {e}")


def on_start_command(intent: Any | None, flags: int, start_id: int) -> int:
    """
    Service onStartCommand callback.
    - Enables auto-restart
    - Initializes ServiceManager
    - Initializes NotificationManager
    - Initializes BroadcastReceiver
    - Starts Service
    """
    global service_manager, receiver
        
    try:
        # Enable auto-restart
        if not PythonService.mService:
            logger.error("PythonService.mService is None")
            return Service.START_STICKY
            
        PythonService.mService.setAutoRestartService(True)

        # Initialize ServiceManager
        if service_manager is None:
            try:
                service_manager = ServiceManager()

                # Initialize NotificationManager
                service_manager._init_notification_manager()
                service_manager.update_foreground_notification_info()
                
                # Initialize BroadcastReceiver
                receiver = create_broadcast_receiver(service_manager)
                if receiver:
                    start_broadcast_receiver(receiver)
                else:
                    logger.error("Failed to create BroadcastReceiver")
                
                # Start Service
                service_manager.run_service()
            
            except Exception as e:
                logger.error(f"Error initializing service: {e}")
                # Clean up
                if service_manager:
                    service_manager.audio_manager.stop_alarm()
                
                service_manager = None
                receiver = None
                return Service.START_STICKY
        
        return Service.START_STICKY
    
    except Exception as e:
        logger.error(f"Error in onStartCommand: {e}")
        return Service.START_STICKY


def on_destroy() -> None:
    """
    Service onDestroy callback.
    - Stops BroadcastReceiver
    - Stops alarm and vibrate
    - Cleans up Service state
    """
    global service_manager, receiver
    
    try:
        # Clean up BroadcastReceiver
        if receiver:
            try:
                receiver.stop()
                        
            except Exception as e:
                logger.error(f"Error stopping BroadcastReceiver: {e}")
        
        # Clean up state
        if service_manager:
            service_manager.stop_alarm_vibrate()
        
        service_manager = None
        receiver = None
        logger.trace("Service destroyed")
        
    except Exception as e:
        logger.error(f"Error in onDestroy: {e}")


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
