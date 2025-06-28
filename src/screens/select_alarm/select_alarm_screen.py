from kivy.clock import Clock
from typing import Any, TYPE_CHECKING

from src.screens.base.base_screen import BaseScreen
from src.screens.select_alarm.select_alarm_utils import ScreenState, BUTTON_STATES

from src.widgets.containers import (Partition, BorderedPartition, CustomButtonRow,
                                    CustomIconButtonRow, CustomSettingsButtonRow)
from src.widgets.buttons import (ConfirmButton, SettingsButton,
                                CancelButton, IconButton, CustomSettingsButton)
from src.widgets.fields import CustomSettingsField
from managers.popups.popup_manager import POPUP
from managers.device.device_manager import DM
from src.utils.logger import logger

from src.settings import STATE

if TYPE_CHECKING:
    from src.app_managers.app_audio_manager import AppAudioManager
    from src.app_managers.app_task_manager import TaskManager
    from src.app_managers.navigation_manager import NavigationManager
    from main import TaskApp


class SelectAlarmScreen(BaseScreen):
    """
    Screen for selecting an alarm.
    """
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager
        self.audio_manager: "AppAudioManager" = app.audio_manager

        self.BUTTON_STATES: dict[ScreenState, dict[str, Any]] = BUTTON_STATES
        self.select_alarm_settings: dict[str, Any] = {
            "alarm_name": None,
            "alarm_path": None,
            "vibrate": False,
            "keep_alarming": False,
        }

        # TopBar title
        self.top_bar.bar_title.set_text("Select Alarm")

        # Saved alarms partition
        self.saved_alarms_partition = Partition()
        # Saved alarms button
        self.saved_alarms_button = SettingsButton(text="Saved Alarms", width=1, color_state=STATE.ACTIVE)
        self.saved_alarms_button.bind(on_release=self.show_saved_alarms_popup)
        self.saved_alarms_partition.add_widget(self.saved_alarms_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.saved_alarms_partition)

        # Recording partition
        self.recording_partition = Partition()
        # Start recording button
        self.start_recording_button = SettingsButton(text="Start Recording", width=1, color_state=STATE.ACTIVE)
        self.start_recording_button.bind(on_release=self.start_recording_alarm)
        self.recording_partition.add_widget(self.start_recording_button)
        # Stop recording button
        self.stop_recording_button = SettingsButton(text="Stop Recording", width=1, color_state=STATE.INACTIVE)
        self.stop_recording_button.bind(on_release=self.stop_recording_alarm)
        self.recording_partition.add_widget(self.stop_recording_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.recording_partition)
        
        # Playback partition
        self.playback_partition = BorderedPartition()
        # Alarm display box
        self.selected_alarm = CustomSettingsField(text="No alarm selected", width=1, color_state=STATE.INACTIVE)
        self.selected_alarm.remove_bottom_radius()
        self.playback_partition.add_widget(self.selected_alarm)
        # Playback button row
        self.playback_row = CustomIconButtonRow()
        # Play selected alarm button
        self.play_selected_alarm_button = IconButton(icon_name="play", color_state=STATE.INACTIVE)
        self.play_selected_alarm_button.bind(on_release=self.play_selected_alarm)
        self.playback_row.add_widget(self.play_selected_alarm_button)
        # Stop selected alarm button
        self.stop_selected_alarm_button = IconButton(icon_name="stop", color_state=STATE.INACTIVE)
        self.stop_selected_alarm_button.bind(on_release=self.stop_selected_alarm)
        self.playback_row.add_widget(self.stop_selected_alarm_button)
        # Edit selected alarm button
        self.rename_selected_alarm_button = IconButton(icon_name="edit", color_state=STATE.INACTIVE)
        self.rename_selected_alarm_button.bind(on_release=self.edit_selected_alarm_name)
        self.playback_row.add_widget(self.rename_selected_alarm_button)
        # Delete selected alarm button
        self.delete_selected_alarm_button = IconButton(icon_name="delete", color_state=STATE.INACTIVE)
        self.delete_selected_alarm_button.bind(on_release=self.delete_selected_alarm)
        self.playback_row.add_widget(self.delete_selected_alarm_button)
        # Deselect alarm button
        self.deselect_alarm_button = CustomSettingsButton(text="Deselect Alarm", width=1, color_state=STATE.INACTIVE)
        self.deselect_alarm_button.remove_top_radius()
        self.deselect_alarm_button.bind(on_release=self.deselect_alarm)
        # Add to scroll container
        self.playback_partition.add_widget(self.playback_row)
        self.playback_partition.add_widget(self.deselect_alarm_button)
        self.scroll_container.container.add_widget(self.playback_partition)

        # Vibrating partition
        self.vibration_partition = Partition()
        # Vibrating button
        self.vibration_button = SettingsButton(text="Vibrate off", width=1, color_state=STATE.INACTIVE)
        self.vibration_button.bind(on_release=self.toggle_vibration)
        self.vibration_partition.add_widget(self.vibration_button)
        # Keep alarming row
        self.keep_alarming_row = CustomSettingsButtonRow()
        self.vibration_partition.add_widget(self.keep_alarming_row)
        # Alarm once button
        self.alarm_once_button = SettingsButton(text="Trigger once", width=2, color_state=STATE.ACTIVE)
        self.alarm_once_button.bind(on_release=self.toggle_keep_alarming)
        self.keep_alarming_row.add_widget(self.alarm_once_button)
        # Alarm continuously button
        self.alarm_continuously_button = SettingsButton(text="Trigger continuously", width=2, color_state=STATE.INACTIVE)
        self.alarm_continuously_button.bind(on_release=self.toggle_keep_alarming)
        self.keep_alarming_row.add_widget(self.alarm_continuously_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.vibration_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=self.cancel_select_alarm)
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = ConfirmButton(text="Select", width=2)
        self.save_button.bind(on_release=self.save_alarm_settings)
        self.button_row.add_widget(self.save_button)
        self.confirmation_partition.add_widget(self.button_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Initialize screen state
        self._screen_state = ScreenState.IDLE
    
    def show_saved_alarms_popup(self, instance=None) -> None:
        """Show a popup with the saved alarms"""
        POPUP.show_selection_popup(
            header="Select alarm",
            current_alarm=self.audio_manager.selected_alarm_name,
            on_confirm=lambda alarm_name: self._select_alarm(alarm_name),
            on_cancel=None,
            options_list=list(self.audio_manager.alarms.keys())
        )
    
    def _select_alarm(self, alarm_name) -> None:
        """Select the alarm and return to NewTaskScreen"""
        if self.audio_manager.select_alarm_audio(alarm_name):
            logger.info(f"Selected alarm: {alarm_name}")
            self.update_selected_alarm_text()
            self.update_playback_partition_states()
            self.update_button_states()
        else:
            logger.info(f"Could not select alarm: {alarm_name}")

    def start_recording_alarm(self, instance) -> None:
        """Start recording an alarm"""
        was_playing: bool = self.audio_manager.audio_player.is_playing()
        self.unschedule_audio_check()
        
        if self.audio_manager.start_recording_audio():
            self.audio_manager.is_recording = True
            self.update_screen_state()
        else:
            self.show_error_popup("Recording Error", "Could not start recording")
            
            # Restore states if recording failed
            if was_playing:
                self.update_button_states()

    def stop_recording_alarm(self, instance) -> None:
        """Stop recording an alarm"""
        if self.audio_manager.stop_recording_audio():
            self.audio_manager.is_recording = False
            self.update_screen_state()
        else:
            self.show_error_popup("Recording Error", "Could not stop recording")

    def play_selected_alarm(self, instance) -> None:
        """Play the selected alarm"""
        if not self.audio_manager.selected_alarm_path:
            self.show_error_popup("Playback Error", "No alarm selected")
            return
        
        if self.audio_manager.start_playing_audio(self.audio_manager.selected_alarm_path):
            self.update_button_states()
            # Update buttons states when audio finishes
            Clock.schedule_interval(self.check_audio_finished, 0.2)
        else:
            self.show_error_popup("Playback Error", "Could not play the selected alarm")

    def stop_selected_alarm(self, instance) -> None:
        """Stop the currently playing alarm"""
        success: bool = self.audio_manager.stop_playing_audio()
        
        if success:
            self.update_button_states()
            self.unschedule_audio_check()
            return False
        
        return True

    def edit_selected_alarm_name(self, instance) -> None:
        """Show a popup to edit the name of the selected alarm."""
        old_name = self.audio_manager.selected_alarm_name
        POPUP.show_input_popup(
            header="Provide new name:",
            input_text=old_name,
            on_confirm=self._handle_alarm_rename,
            on_cancel=None
        )
    
    def _handle_alarm_rename(self, new_name: str) -> None:
        """
        Handles alarm rename callback.
        Validates new name and shows error popup if invalid or
         changes name if valid.
        """
        # No change
        if new_name == self.audio_manager.selected_alarm_name:
            return
        
        # Name taken
        if new_name in self.audio_manager.alarms:
            message = "Name already taken"
            Clock.schedule_once(lambda dt: self._handle_alarm_rename_error(invalid_name=new_name,
                                                                           message=message), 0.3)
            return
        
        # Name too long
        if len(new_name) > DM.SETTINGS.ALARM_NAME_MAX_LENGTH:
            message = f"Name is longer than {DM.SETTINGS.ALARM_NAME_MAX_LENGTH} characters"
            Clock.schedule_once(lambda dt: self._handle_alarm_rename_error(invalid_name=new_name,
                                                                           message=message), 0.3)
            return
        
        # Name too short
        if len(new_name) < DM.SETTINGS.ALARM_NAME_MIN_LENGTH:
            message = f"Name is shorter than {DM.SETTINGS.ALARM_NAME_MIN_LENGTH} characters"
            Clock.schedule_once(lambda dt: self._handle_alarm_rename_error(invalid_name=new_name,
                                                                           message=message), 0.3)
            return
        
        self._rename_alarm(new_name)
    
    def _handle_alarm_rename_error(self, invalid_name: str, message: str, *args, **kwargs) -> None:
        """Shows input popup with error message and invalid name."""
        header = f"{message}\nProvide different name:"
        POPUP.show_input_popup(
            header=header,
            input_text=invalid_name,
            on_confirm=self._handle_alarm_rename,
            on_cancel=None
        )

    def _rename_alarm(self, new_name: str) -> None:
        """Rename the selected alarm"""
        logger.debug(f"Renaming alarm from {self.audio_manager.selected_alarm_name} to {new_name}")
        self.audio_manager.update_alarm_name(new_name)
        self.update_selected_alarm_text()

    def delete_selected_alarm(self, instance) -> None:
        """Show a popup to delete the selected alarm"""
        POPUP.show_confirmation_popup(
            header="Delete this alarm?",
            field_text=self.audio_manager.selected_alarm_name,
            on_confirm=self._handle_alarm_delete,
            on_cancel=None
        )
        
    def _handle_alarm_delete(self) -> None:
        """Handle alarm deletion"""
        self.audio_manager.delete_alarm(self.audio_manager.selected_alarm_name)
    
    def load_task_vibrate_state(self) -> None:
        """Load the vibrate state of the task to edit"""
        self.set_button_state(
            self.vibration_button, 
            active=self.audio_manager.selected_vibrate, 
            enabled=True,
            text="Vibrate on" if self.audio_manager.selected_vibrate else "Vibrate off"
        )

    def toggle_vibration(self, instance) -> None:
        """Toggle vibration on the selected alarm"""
        self.audio_manager.selected_vibrate = not self.audio_manager.selected_vibrate
        self.set_button_state(
            self.vibration_button,
            active=self.audio_manager.selected_vibrate,
            text="Vibrate on" if self.audio_manager.selected_vibrate else "Vibrate off"
        )
    
    def toggle_keep_alarming(self, instance) -> None:
        """Toggle keep alarming on the selected alarm"""
        self.audio_manager.selected_keep_alarming = not self.audio_manager.selected_keep_alarming
        self.update_keep_alarming_states()

    def cancel_select_alarm(self, instance) -> None:
        """
        Reset the selected_alarm and navigate back to the NewTaskScreen.
        """
        self.unschedule_audio_check()

        current_alarm_settings = self._get_select_alarm_settings()
        if current_alarm_settings != self.select_alarm_settings:
            self._restore_select_alarm_state()
        
        self.navigation_manager.navigate_back_to(DM.SCREEN.NEW_TASK)
    
    def save_alarm_settings(self, instance) -> None:
        """Save the alarm settings and return to NewTaskScreen"""
        self.unschedule_audio_check()
        self.navigation_manager.navigate_back_to(DM.SCREEN.NEW_TASK)
    
    def deselect_alarm(self, instance) -> None:
        """Deselect the alarm and return to NewTaskScreen"""
        self.unschedule_audio_check()
        self.audio_manager.selected_alarm_name = None
        self.audio_manager.selected_alarm_path = None
        self.update_screen_state()
    
    def check_audio_finished(self, dt: float) -> bool:
        """Check if audio has finished playing and update buttons accordingly"""
        if not self.audio_manager.audio_player.is_playing():
            self.update_button_states()
            self.unschedule_audio_check()
            return False
        
        return True

    def on_pre_enter(self) -> None:
        """Called when the screen is entered"""
        super().on_pre_enter()

        self._set_select_alarm_settings()
        self.update_screen_state()
    
    def _set_select_alarm_settings(self) -> None:
        """
        Saves the selected alarm settings if coming from NewTaskScreen.
        Saves: alarm name, alarm path, vibrate, keep alarming.
        Allows proper handeling of canceling when changes are made.
        """
        prev_screen = self.app.navigation_manager.history[-2]
        if prev_screen == DM.SCREEN.NEW_TASK:
            self.select_alarm_settings = self._get_select_alarm_settings()
    
    def _get_select_alarm_settings(self) -> dict[str, Any]:
        """Get the current selected alarm settings"""
        return {
            "alarm_name": self.audio_manager.selected_alarm_name,
            "alarm_path": self.audio_manager.selected_alarm_path,
            "vibrate": self.audio_manager.selected_vibrate,
            "keep_alarming": self.audio_manager.selected_keep_alarming,
        }
    
    def _restore_select_alarm_state(self) -> None:
        """Restore the selected alarm settings"""
        self.audio_manager.selected_alarm_name = self.select_alarm_settings["alarm_name"]
        self.audio_manager.selected_alarm_path = self.select_alarm_settings["alarm_path"]
        self.audio_manager.selected_vibrate = self.select_alarm_settings["vibrate"]
        self.audio_manager.selected_keep_alarming = self.select_alarm_settings["keep_alarming"]

    def on_enter(self) -> None:
        """Called when the screen is entered"""
        super().on_enter()
    
    def on_leave(self) -> None:
        """Called when the screen is left"""
        super().on_leave()
        # Stop any playing audio and remove scheduled checks
        self.audio_manager.stop_playing_audio()
        self.unschedule_audio_check()
    
    @property
    def screen_state(self) -> ScreenState:
        """Get the current ScreenState based on AppAudioManager state"""
        if self.audio_manager.is_recording:
            return ScreenState.RECORDING
        elif self.audio_manager.audio_player.is_playing():
            return ScreenState.PLAYING
        elif self.audio_manager.selected_alarm_name is not None:
            return ScreenState.ALARM_SELECTED
        return ScreenState.IDLE
    
    def update_playback_partition_states(self) -> None:
        """Update playback_partition and selected_alarm states"""
        has_content = self.screen_state != ScreenState.IDLE
        self.playback_partition.set_active() if has_content else self.playback_partition.set_inactive()
        self.selected_alarm.set_active() if has_content else self.selected_alarm.set_inactive()
    
    def update_selected_alarm_text(self) -> None:
        """Update the selected_alarm text based on current ScreenState"""
        current_state = self.screen_state
        if current_state == ScreenState.RECORDING:
            self.selected_alarm.set_text("Recording...")
        elif current_state == ScreenState.IDLE:
            self.selected_alarm.set_text("No alarm selected")
        else:
            self.selected_alarm.set_text(self.audio_manager.selected_alarm_name)
    
    def update_keep_alarming_states(self) -> None:
        """Update the keep_alarming states"""
        self.set_button_state(
            self.alarm_once_button,
            active=not self.audio_manager.selected_keep_alarming,
            enabled=self.audio_manager.selected_keep_alarming
        )
        self.set_button_state(
            self.alarm_continuously_button,
            active=self.audio_manager.selected_keep_alarming,
            enabled=not self.audio_manager.selected_keep_alarming
        )
    
    def update_button_states(self) -> None:
        """Update all button states based on current ScreenState"""
        current_state = self.screen_state
        state_config = self.BUTTON_STATES[current_state]
        
        self.set_button_state(self.start_recording_button, **state_config["start_recording"])
        self.set_button_state(self.stop_recording_button, **state_config["stop_recording"])
        self.set_button_state(self.play_selected_alarm_button, **state_config["play"])
        self.set_button_state(self.stop_selected_alarm_button, **state_config["stop"])
        self.set_button_state(self.rename_selected_alarm_button, **state_config["rename"])
        self.set_button_state(self.delete_selected_alarm_button, **state_config["delete"])
        self.set_button_state(self.save_button, **state_config["save"])
        self.set_button_state(self.deselect_alarm_button, **state_config["deselect"])
    
    def update_screen_state(self) -> None:
        """Update all UI elements based on current ScreenState"""
        self.update_playback_partition_states()
        self.update_selected_alarm_text()
        self.update_keep_alarming_states()
        self.update_button_states()
        self.load_task_vibrate_state()

    def unschedule_audio_check(self):
        """Unschedule the audio finished check."""
        Clock.unschedule(self.check_audio_finished)