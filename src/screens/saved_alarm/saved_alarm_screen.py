from src.screens.base.base_screen import BaseScreen

from src.widgets.containers import Partition, ScrollContainer, CustomButtonRow
from src.widgets.buttons import (CustomConfirmButton, CustomSettingsButton,
                                 CustomCancelButton)

from src.utils.logger import logger

from src.settings import STATE, SCREEN


class SavedAlarmScreen(BaseScreen):
    """
    SavedAlarmScreen is the screen for selecting a saved alarm that:
    - Has a top bar with a back button, options button, and exit button.
    - Has a alarm picker partition.
    - Has a confirmation partition.
    """
    def __init__(self, navigation_manager, task_manager, audio_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.audio_manager = audio_manager

        # TopBar title
        self.top_bar.bar_title.set_text("Saved Alarms")

        # Alarm picker partition
        self.alarm_picker_partition = Partition()
        # Alarm picker buttons
        
        # Add to scroll container
        self.scroll_container.container.add_widget(self.alarm_picker_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.confirmation_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel")
        self.cancel_button.bind(on_release=self.cancel_alarm_selection)
        self.confirmation_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Select")
        self.confirm_button.bind(on_release=self.confirm_alarm_selection)
        self.confirmation_row.add_widget(self.confirm_button)
        # Add to confirmation partition
        self.confirmation_partition.add_widget(self.confirmation_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add bottom bar
        self.add_bottom_bar()

    def confirm_alarm_selection(self, instance) -> None:
        """Confirm the alarm selection."""
        if self.audio_manager.selected_alarm_name is not None:
            self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM)
        
        else:
            self.show_error_popup("Selection Error", "No alarm selected")
    
    def cancel_alarm_selection(self, instance) -> None:
        """
        Cancel the alarm selection.
        """
        self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM)

    def create_alarm_buttons(self) -> None:
        """
        Create the alarm buttons for the AlarmPicker partition.
        """
        for name, path in self.audio_manager.alarms.items():
            button = CustomSettingsButton(
                text=name,
                width=1,
                color_state=STATE.INACTIVE,
            )
            button.bind(on_release=self.select_saved_alarm)
            self.alarm_picker_partition.add_widget(button)

    def select_saved_alarm(self, instance) -> None:
        """
        Callback for saved alarm buttons.
        Select the alarm and update the button states.
        """
        if self.audio_manager.select_alarm_audio(name=instance.text):
            self.update_button_states()
        else:
            logger.error(f"Failed to select alarm: {instance.text}")
            self.show_error_popup("Selection Error", "No alarm selected")

    def update_button_states(self) -> None:
        """
        Sets the states of the alarm buttons and the confirm button.
        The selected alarm gets state=ACTIVE, all other buttons get state=INACTIVE.
        The confirm button gets state=ACTIVE if an alarm is selected.
        """
        # Use provided name or get from audio_manager
        selected_alarm_name = self.audio_manager.selected_alarm_name
        
        # Update alarm buttons
        for button in self.alarm_picker_partition.children:
            if selected_alarm_name and button.text == selected_alarm_name:
                button.set_active_state()
            else:
                button.set_inactive_state()
        
        # Update confirm button
        if selected_alarm_name:
            self.confirm_button.set_active_state()
        else:
            self.confirm_button.set_inactive_state()

    def on_pre_enter(self) -> None:
        """
        Called when the screen is entered.
        """
        super().on_pre_enter()
        self.alarm_picker_partition.clear_widgets()
        self.create_alarm_buttons()
        self.update_button_states()
