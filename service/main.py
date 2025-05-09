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
                    logger.debug(f"BGTaskService: Received broadcast action: {pure_action}")
                    service_manager.handle_action(pure_action)
            except Exception as e:
                logger.error(f"BGTaskService: Error in broadcast receiver: {e}")
        
        # Register actions the receiver should listen for
        actions = [
            f"{package_name}.{ACTION.SNOOZE_A}",
            f"{package_name}.{ACTION.STOP}"
        ]
        
        receiver = BroadcastReceiver(on_receive, actions=actions)
        receiver.start()
        logger.debug("BGTaskService: Registered action broadcast receiver")
        
        return receiver
        
    except Exception as e:
        logger.error(f"BGTaskService: Error setting up broadcast receiver: {e}")
        return None


def start_monitoring_service(service_manager):
    """Initializes and starts the monitoring service with active Task"""
    service_manager.init_notification_manager()
    task = service_manager.service_task_manager.current_task
    timestamp = get_service_timestamp(task.timestamp)    
    # Startup notification
    service_manager.notification_manager.show_foreground_notification(
        "BGTask Service",
        f"Next Task expires at:\n{timestamp}",
        with_buttons=True
    )
    
    logger.debug("BGTaskService: Starting main service loop")
    service_manager.run_service()


def show_idle_notification(service_manager):
    """Shows notification when no Tasks are available to monitor"""
    service_manager.init_notification_manager()
    service_manager.notification_manager.show_foreground_notification(
        "BGTask Service",
        "No Tasks to monitor",
        with_buttons=False
    )


def main():
    """Main entry point for the background service"""
    logger.debug("BGTaskService: Starting background service")
    
    # Initialize ServiceManager
    service_manager = ServiceManager()
    service_manager.remove_stop_flag()
    
    # Set up broadcast receiver
    receiver = create_broadcast_receiver(service_manager)
    
    try:
        # Check if we have a Task to monitor
        if service_manager.service_task_manager.current_task is not None:
            start_monitoring_service(service_manager)
        else:
            show_idle_notification(service_manager)
            
    finally:
        # Stop receiver
        if receiver:
            receiver.stop()
        logger.debug("BGTaskService: Service stopping")


if __name__ == "__main__":
    main()
    logger.debug("BGTaskService: Service stopped")
