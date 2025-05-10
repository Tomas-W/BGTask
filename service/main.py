from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass                      # type: ignore

from service.service_manager import ServiceManager
from service.service_logger import logger
from service.utils import ACTION, get_service_timestamp

PythonService = autoclass("org.kivy.android.PythonService")


def create_broadcast_receiver(service_manager):
    """Creates and starts a broadcast receiver for handling notification actions"""
    try:
        context = PythonService.mService.getApplicationContext()
        package_name = context.getPackageName()
        
        def on_receive(context, intent):
            """Callback for handling received broadcast actions"""
            try:
                action = intent.getAction()
                if action:
                    pure_action = action.split(".")[-1]
                    logger.debug(f"Received broadcast action: {pure_action}")
                    service_manager.handle_action(pure_action)
            except Exception as e:
                logger.error(f"Error in broadcast receiver: {e}")
        
        # Register actions the receiver should listen for
        actions = [
            f"{package_name}.{ACTION.SNOOZE_A}",
            f"{package_name}.{ACTION.STOP}"
        ]
        
        receiver = BroadcastReceiver(on_receive, actions=actions)
        receiver.start()
        logger.debug("Registered action broadcast receiver")
        
        return receiver
        
    except Exception as e:
        logger.error(f"Error setting up broadcast receiver: {e}")
        return None


def start_monitoring_service(service_manager):
    """Initializes and starts the monitoring service with active Task"""
    service_manager.init_notification_manager()
    
    logger.debug("Starting main service loop")
    service_manager.run_service()


def main():
    """Main entry point for the background service"""
    logger.debug("Starting background service")
    
    # Initialize ServiceManager
    service_manager = ServiceManager()
    
    # Set up broadcast receiver
    receiver = create_broadcast_receiver(service_manager)
    
    try:
        # Initialize notification manager and show appropriate notification
        service_manager.init_notification_manager()
        service_manager.update_foreground_notification()
        
        # Start monitoring if we have tasks
        if service_manager.service_task_manager.current_task is not None:
            start_monitoring_service(service_manager)
            
    finally:
        # Stop receiver
        if receiver:
            receiver.stop()
        logger.debug("Service stopping")


if __name__ == "__main__":
    main()
    logger.debug("Service stopped")
