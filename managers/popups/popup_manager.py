from typing import Callable, TYPE_CHECKING

from kivy.clock import Clock

from managers.popups.task_popup import TaskPopup
from managers.popups.custom_popup import CustomPopup
from managers.popups.confirmation_popup import ConfirmationPopup
from managers.popups.text_input_popup import TextInputPopup

from managers.device.device_manager import DM
from src.utils.logger import logger


if TYPE_CHECKING:
    from main import TaskApp


class PopupManager:
    def __init__(self, app: "TaskApp"):
        self.app = app
        self.task_manager = app.task_manager
        self.expiry_manager = app.expiry_manager
        
        self.custom = CustomPopup()
        self.confirmation = ConfirmationPopup()
        self.input = TextInputPopup()
        self.task = TaskPopup()
    
    def _handle_task_popup(self, *args, **kwargs):
        """
        Handle showing TaskPopup when a Task expires.
        Configures callbacks for:
        - Stop alarm
        - Snooze alarm
        """
        task = kwargs.get("task") if "task" in kwargs else args[0]
        if not task:
            logger.error("Error showing TaskPopup, no task provided")
            return
        
        # Update popup callbacks
        self.task.update_callbacks(
            on_confirm=lambda: self._snooze_alarm(task.task_id),
            on_cancel=lambda: self._stop_alarm(task.task_id)
        )
        
        # Show the popup
        self.show_task_popup(task=task)
    
    def _stop_alarm(self, task_id: str):
        """Stop the alarm and mark task as expired"""
        self.app.expiry_manager.cancel_task(task_id=task_id)
    
    def _snooze_alarm(self, task_id: str):
        """Snooze the alarm"""
        self.app.expiry_manager.snooze_task(DM.ACTION.SNOOZE_A, task_id)

    def _handle_popup_confirmation(self, confirmed: bool):
        """Handle confirmation popup button press"""
        if self.callback:
            self.callback(confirmed)

    def _handle_popup_text_input(self, confirmed: bool):
        """Handle text input popup button press"""
        if self.callback:
            text = self.input.input_field.text if confirmed else None
            self.callback(text)
    
    def show_custom_popup(self, header: str, field_text: str, extra_info: str, confirm_text: str,
                          on_confirm: Callable, on_cancel: Callable):
        """
        Show a CustomPopup with a:
        - Header [aligned left]
        - Info field
        - Extra info [aligned left]
        - ConfirmButton and CancelButton.
        """
        self.custom.header.text = header
        self.custom.extra_info.text = extra_info
        self.custom.update_field_text(field_text)
        self.custom.confirm_button.set_text(confirm_text)
        self.custom.update_callbacks(on_confirm, on_cancel)
        self.custom.show_animation()

    def show_confirmation_popup(self, header: str, field_text: str,
                                 on_confirm: Callable, on_cancel: Callable):
        """
        Show a ConfirmationPopup with a:
        - Header [aligned left]
        - Info field
        - ConfirmButton and CancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.confirmation.header.text = header
        self.confirmation.update_field_text(field_text)
        self.confirmation.update_callbacks(on_confirm, on_cancel)
        self.confirmation.show_animation()

    def show_input_popup(self, header: str, input_text: str,
                         on_confirm: Callable, on_cancel: Callable):
        """
        Show a TextInputPopup with a:
        - Header [aligned left]
        - Input field
        - ConfirmButton and CancelButton.
        Reuses the same popup instance for efficiency.
        """
        self.input.header.text = header
        self.input.input_field.text = input_text
        self.input.update_callbacks(on_confirm, on_cancel)
        self.input.show_animation()
    
    def show_task_popup(self, *args, **kwargs):
        """
        Show a TaskPopup with a:
        - Header [aligned center]
        - TaskContainer
          |- TimeLabel
          |- TaskLabel
        - StopButton and SnoozeButton
        """
        task = kwargs.get("task") if "task" in kwargs else args[-1]

        def show_popup(dt):
            self.task.task_label.set_task_details(task)
            
            def display_new_popup(dt):
                self.app.active_popup = self.task
                self.task.show_animation()
            
            # Close any existing popups
            if hasattr(self.app, "active_popup") and self.app.active_popup:
                self.app.active_popup.dismiss()
                # Schedule new popup to show after a small delay
                Clock.schedule_once(display_new_popup, 0.3)
            else:
                # No existing popup, show immediately
                display_new_popup(0)
        
        Clock.schedule_once(show_popup, 0)

    def _show_task_popup(self, task, on_confirm=None, on_cancel=None):
        """Internal callback for handling the TaskPopup."""        
        self.task.update_callbacks(
            on_confirm=on_confirm,
            on_cancel=on_cancel
        )
        self.show_task_popup(task=task)


def _init_popup_manager(app: "TaskApp"):
    global POPUP
    POPUP = PopupManager(app=app)


POPUP = None
