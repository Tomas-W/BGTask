from typing import Callable, TYPE_CHECKING

from kivy.clock import Clock

from managers.popups.task_popup import TaskPopup
from managers.popups.confirmation_popup import ConfirmationPopup
from managers.popups.custom_popup import CustomPopup
from managers.popups.text_input_popup import TextInputPopup
from managers.popups.selection_popup import SelectionPopup

from managers.device.device_manager import DM
from src.utils.logger import logger


if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.app_task_manager import TaskManager
    from src.app_managers.app_expiry_manager import ExpiryManager
    from managers.tasks.task import Task


class PopupManager:
    """
    Manages the display of popups. All popups have a header and:
    - TaskPopup: a Task's details & snooze / cancel buttons
    - ConfirmationPopup: a message & confirm / cancel buttons
    - CustomPopup: ConfirmationPopup with extra info above the buttons
    - TextInputPopup: a text input field & confirm / cancel buttons
    """
    def __init__(self, app: "TaskApp"):
        self.app: "TaskApp" = app
        self.task_manager: "TaskManager" = app.task_manager
        self.expiry_manager: "ExpiryManager" = app.expiry_manager
        
        self.task_popup: TaskPopup = TaskPopup()
        self.confirmation_popup: ConfirmationPopup = ConfirmationPopup()
        self.custom_popup: CustomPopup = CustomPopup()
        self.input_popup: TextInputPopup = TextInputPopup()
        self.selection_popup: SelectionPopup = SelectionPopup()
    
    def show_task_popup(self, task: "Task") -> None:
        """
        Sets up popup callbacks and shows the TaskPopup.
        """
        if not DM.LOADED.TASK_POPUP:
            self.task_popup._init_content()
                
        # Update callbacks
        self.task_popup.update_callbacks(
            snooze_a=lambda: self._snooze_a_task(task.task_id),
            snooze_b=lambda: self._snooze_b_task(task.task_id),
            cancel=lambda: self._cancel_task(task.task_id)
        )
        self._show_task_popup(task=task)
    
    def _show_task_popup(self, task: "Task") -> None:
        """
        Show a TaskPopup with a:
        - Header [aligned center]
        - TaskContainer
          |- TimeLabel
          |- TaskLabel
        - SnoozeAButton and SnoozeBButton
        - CancelButton
        """
        def show_popup(dt: float) -> None:
            self.task_popup.task_label.set_task_details(task)
            
            def display_new_popup(dt: float) -> None:
                self.app.active_popup = self.task_popup
                self.task_popup.show_animation()
            
            # Close existing popups
            # Should not happen as ExpiryManager doesnt show new Popups
            # without user handeling previous one
            if hasattr(self.app, "active_popup") and self.app.active_popup:
                self.app.active_popup.dismiss()
                # Schedule popup
                Clock.schedule_once(display_new_popup, 0.3)
            else:
                # Show immediately
                display_new_popup(0)
        
        Clock.schedule_once(show_popup, 0)
        logger.debug(f"Displaying TaskPopup: {DM.get_task_id_log(task.task_id)}")
    
    def show_confirmation_popup(self, header: str, field_text: str,
                                 on_confirm: Callable, on_cancel: Callable) -> None:
        """
        Show a ConfirmationPopup with a:
        - Header [aligned left]
        - Info field
        - ConfirmButton and CancelButton.
        """
        if not DM.LOADED.CONFIRMATION_POPUP:
            self.confirmation_popup._init_content()
        
        self.confirmation_popup.header.text = header
        self.confirmation_popup.update_field_text(field_text)
        self.confirmation_popup.update_callbacks(on_confirm, on_cancel)
        self.confirmation_popup.show_animation()
        logger.trace(f"Displaying ConfirmationPopup: {header}")
    
    def show_custom_popup(self, header: str, field_text: str, extra_info: str,
                          confirm_text: str, on_confirm: Callable, on_cancel: Callable) -> None:
        """
        Show a CustomPopup with a:
        - Header [aligned left]
        - Info field
        - Extra info [aligned left]
        - ConfirmButton and CancelButton.
        """
        if not DM.LOADED.CUSTOM_POPUP:
            self.custom_popup._init_content()
        
        self.custom_popup.header.text = header
        self.custom_popup.update_field_text(field_text)
        self.custom_popup.extra_info.text = extra_info
        self.custom_popup.confirm_button.set_text(confirm_text)
        self.custom_popup.update_callbacks(on_confirm, on_cancel)
        self.custom_popup.show_animation()
        logger.trace(f"Displaying CustomPopup: {header} {field_text}")

    def show_input_popup(self, header: str, input_text: str,
                         on_confirm: Callable, on_cancel: Callable) -> None:
        """
        Show a TextInputPopup with a:
        - Header [aligned left]
        - Input field
        - ConfirmButton and CancelButton.
        """
        if not DM.LOADED.INPUT_POPUP:
            self.input_popup._init_content()
        
        self.input_popup.header.text = header
        self.input_popup.input_field.text = input_text
        self.input_popup.update_callbacks(on_confirm, on_cancel)
        self.input_popup.show_animation()
        logger.trace(f"Displaying TextInputPopup: {header}")
    
    def show_selection_popup(self, header: str, options_list: list, current_selection: str,
                             on_confirm: Callable, on_cancel: Callable) -> None:
        """
        Show a SelectionPopup with a:
        - Header [aligned center]
        - Scrollable list of SettingsButton options
        - ConfirmButton and CancelButton.
        """
        if not DM.LOADED.SELECTION_POPUP:
            self.selection_popup._init_content()
        
        self.selection_popup.header.text = header
        # self.selection_popup.current_selection = current_selection
        self.selection_popup.populate_selection_buttons(options_list, current_selection)
        self.selection_popup.update_callbacks(on_confirm, on_cancel)
        self.selection_popup.show_animation()
        logger.trace(f"Displaying SelectionPopup: {header}")
    
    def _cancel_task(self, task_id: str) -> None:
        """Calls CANCEL on ExpiryManager."""
        self.app.expiry_manager.cancel_task(task_id=task_id)
    
    def _snooze_a_task(self, task_id: str) -> None:
        """Calls SNOOZE with SNOOZE_A on ExpiryManager."""
        self.app.expiry_manager.snooze_task(DM.ACTION.SNOOZE_A, task_id)

    
    def _snooze_b_task(self, task_id: str) -> None:
        """Calls SNOOZE with SNOOZE_B on ExpiryManager."""
        self.app.expiry_manager.snooze_task(DM.ACTION.SNOOZE_B, task_id)

    def _handle_popup_confirmation(self, confirmed: bool) -> None:
        """Handle confirmation Popup button press"""
        if self.callback:
            self.callback(confirmed)

    def _handle_popup_text_input(self, confirmed: bool) -> None:
        """Handle text input from TextInputPopup."""
        logger.critical(f"Confirmed: {confirmed}")
        if self.callback:
            text = self.input_popup.input_field.text if confirmed else None
            self.callback(text)


def _init_popup_manager(app: "TaskApp"):
    global POPUP
    POPUP = PopupManager(app=app)


POPUP = None
