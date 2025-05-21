from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore
from typing import Any

from service.service_manager import ServiceManager
from service.service_utils import ACTION

from src.utils.logger import logger

PythonService = autoclass("org.kivy.android.PythonService")
Service = autoclass("android.app.Service")


# Global service manager instance
service_manager: ServiceManager | None = None
receiver: BroadcastReceiver | None = None

def create_broadcast_receiver(service_manager: ServiceManager) -> Any | None:
    """Creates a broadcast receiver for handling notification actions"""
    try:
        context = PythonService.mService.getApplicationContext()
        if not context:
            logger.error("Failed to get application context")
            return None
            
        package_name = context.getPackageName()
        if not package_name:
            logger.error("Failed to get package name")
            return None
        
        def on_receive(context: Any, intent: Any) -> None:
            """Callback for handling received broadcast actions"""
            try:
                action = intent.getAction()
                if action:
                    pure_action = action.split(".")[-1]
                    logger.debug(f"Received broadcast action: {pure_action}")
                    service_manager.handle_action(pure_action)
            
            except Exception as e:
                logger.error(f"Error in broadcast receiver: {e}")
        
        # Register actions to receiver
        actions = [
            f"{package_name}.{ACTION.SNOOZE_A}",
            f"{package_name}.{ACTION.CANCEL}",
            f"{package_name}.{ACTION.OPEN_APP}"
        ]
        
        receiver = BroadcastReceiver(on_receive, actions=actions)
        logger.debug("Created BroadcastReceiver")
        return receiver
        
    except Exception as e:
        logger.error(f"Error setting up broadcast receiver: {e}")
        return None


def start_broadcast_receiver(receiver: Any) -> None:
    """Starts the broadcast receiver"""
    try:
        receiver.start()
        logger.debug("Started BroadcastReceiver")
    
    except Exception as e:
        logger.error(f"Error starting broadcast receiver: {e}")


def on_start_command(intent: Any, flags: int, start_id: int) -> int:
    """
    Service onStartCommand callback.
    Enables auto-restart, initializes components,
    and shows foreground notification.
    """
    global service_manager, receiver
    
    logger.debug(f"Service onStartCommand: flags={flags}, startId={start_id}")
    
    try:
        # Enable auto-restart
        if not PythonService.mService:
            logger.error("PythonService not available")
            return Service.START_STICKY
            
        PythonService.mService.setAutoRestartService(True)
        
        # Initialize service components
        if service_manager is None:
            try:
                service_manager = ServiceManager()
                service_manager._init_notification_manager()
                
                # Show foreground notification
                service_manager.update_foreground_notification_info()
                # Set up broadcast receiver
                receiver = create_broadcast_receiver(service_manager)
                if receiver:
                    start_broadcast_receiver(receiver)
                else:
                    logger.error("Failed to create broadcast receiver")
                
                # Start monitoring
                service_manager.run_service()
            
            except Exception as e:
                logger.error(f"Error initializing service: {e}")
                # Clean up on initialization failure
                if service_manager:
                    service_manager.stop_alarm_vibrate()
                
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
    Cleans up receiver, stops alarm vibrate,
    and stops the service.
    """
    global service_manager, receiver
    
    logger.debug("Service onDestroy called")
    
    try:
        # Clean up receiver
        if receiver:
            try:
                receiver.stop()
                        
            except Exception as e:
                logger.error(f"Error stopping broadcast receiver: {e}")
        
        # Clean up state
        if service_manager:
            service_manager.stop_alarm_vibrate()
        
        service_manager = None
        receiver = None
        
    except Exception as e:
        logger.error(f"Error in onDestroy: {e}")


def main() -> None:
    """Main entry point for the background service"""
    try:
        logger.debug("Starting background service")
        on_start_command(None, 0, 1)
    
    except Exception as e:
        logger.error(f"Error in Service main: {e}")
        on_destroy()


if __name__ == "__main__":
    main()
