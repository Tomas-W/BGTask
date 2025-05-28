from src.managers.app_device_manager import DM
from src.utils.logger import logger


class AppCommunicationManager:
    def __init__(self):
        pass

    def _validate_action(self, action: str) -> bool:
        return hasattr(DM.ACTION, action)

    def send_action(self, action: str):
        if not DM.is_android:
            logger.debug("Not Android, skipping action")
            return
        
        if not self._validate_action(action):
            logger.error(f"Invalid action: {action}")
            return

        try:
            from jnius import autoclass # type: ignore
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            intent = Intent()
            intent.setAction(f"{context.getPackageName()}.{action}")
            context.sendBroadcast(intent)
            logger.debug(f"Sent broadcast: {action}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")

    def receive_message(self, message: str):
        pass