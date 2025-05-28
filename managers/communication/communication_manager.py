from typing import Any, Callable

from android.broadcast import BroadcastReceiver  # type: ignore
from jnius import autoclass  # type: ignore

from managers.device.device_manager import DM
from src.utils.logger import logger

Intent = autoclass("android.content.Intent")
PythonService = autoclass("org.kivy.android.PythonService")
PythonActivity = autoclass("org.kivy.android.PythonActivity")


class Communicator:
    """
    Handles all communication between the app and background service.
    - Service to App: Sends broadcasts from service to app
    - App to Service: Receives broadcasts from app to service
    """
    def __init__(self):
        # For app-to-service communication
        self.receiver: BroadcastReceiver | None = None
        self._message_handler: Callable[[str, dict], None] | None = None
        
        # Initialize context based on where we are
        self._init_context()
        
        # Initialize the receiver if we're in the app
        if DM.is_android and hasattr(PythonActivity, "mActivity"):
            self._init_receiver()
    
    def _init_context(self) -> None:
        """Initialize the appropriate context based on whether we're in the app or service"""
        try:
            # Try service context first
            if hasattr(PythonService, "mService") and PythonService.mService:
                self._context = PythonService.mService.getApplicationContext()
                logger.debug("Initialized with service context")
            # Fall back to app context
            elif hasattr(PythonActivity, "mActivity") and PythonActivity.mActivity:
                self._context = PythonActivity.mActivity
                logger.debug("Initialized with app context")
            else:
                logger.error("Could not initialize context - neither service nor app context available")
                self._context = None
                return
                
            self._package_name = self._context.getPackageName()
            
        except Exception as e:
            logger.error(f"Error initializing context: {e}")
            self._context = None
            self._package_name = None
    
    def _init_receiver(self) -> None:
        """Initialize broadcast receiver for service messages"""
        if not self._context:
            logger.error("Cannot initialize receiver - no context available")
            return
            
        try:
            # Define the actions we want to receive
            actions = [
                f"{self._package_name}.{DM.ACTION.SCROLL_TO_EXPIRED}",
            ]
            
            # Create receiver with callback
            self.receiver = BroadcastReceiver(self._on_service_message, actions=actions)
            self.receiver.start()
            logger.debug("Started service message receiver")
            
        except Exception as e:
            logger.error(f"Error initializing service receiver: {e}")
    
    def _on_service_message(self, context: Any, intent: Any) -> None:
        """Handle messages from the service"""
        try:
            action = intent.getAction()
            if not action:
                return
                
            pure_action = action.split(".")[-1]
            
            if not self._message_handler:
                logger.error("Message handler not set, cannot handle service message")
                return
            
            # Extract extras from intent
            extras = {}
            if intent.hasExtra("task_id"):
                extras["task_id"] = intent.getStringExtra("task_id")
            # Add more extras as needed
            
            # Call the message handler
            self._message_handler(pure_action, extras)
            logger.debug(f"Handled service message: {pure_action}")
                
        except Exception as e:
            logger.error(f"Error handling service message: {e}")
    
    def set_message_handler(self, handler: Callable[[str, dict], None]) -> None:
        """
        Set the function that will handle messages from the service.
        
        Args:
            handler: Function that takes (action: str, extras: dict) parameters
        """
        self._message_handler = handler
    
    def send_broadcast_to_app(self, action: str, extras: dict = None) -> None:
        """
        Send a broadcast from the service to the app.
        
        Args:
            action: The action to broadcast (e.g. TASK_EXPIRED)
            extras: Optional dictionary of extra data to include in the broadcast
        """
        if not self._context:
            logger.error("Cannot send broadcast - no context available")
            return
            
        try:
            intent = Intent()
            intent.setAction(f"{self._package_name}.{action}")
            intent.setPackage(self._package_name)
            
            # Add any extra data
            if extras:
                for key, value in extras.items():
                    if isinstance(value, str):
                        intent.putExtra(key, value)
                    elif isinstance(value, int):
                        intent.putExtra(key, value)
                    # Add more types as needed
            
            self._context.sendBroadcast(intent)
            logger.debug(f"Service sent broadcast to app: {action}")
            
        except Exception as e:
            logger.error(f"Error sending broadcast to app: {e}")
    
    def stop(self) -> None:
        """Stop the service broadcast receiver"""
        if self.receiver:
            try:
                self.receiver.stop()
                self.receiver = None
                logger.debug("Stopped service message receiver")
            except Exception as e:
                logger.error(f"Error stopping service receiver: {e}")


# Global instance
_communicator: Communicator | None = None


def get_communicator() -> Communicator:
    """Get or create the global communicator instance"""
    global _communicator
    if _communicator is None:
        _communicator = Communicator()
    return _communicator
