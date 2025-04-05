from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from src.widgets.containers import (ScrollContainer, Partition,
                                    CustomButtonRow, CustomSettingsButtonsRow)
from src.widgets.buttons import (CustomConfirmButton, CustomSettingsButton,
                                CustomCancelButton)
from src.widgets.fields import SettingsField

from src.utils.logger import logger

from src.settings import STATE, SCREEN


class SelectAlarmScreen(BaseScreen):
    """
    Screen for selecting an alarm.
    """
    def __init__(self, navigation_manager, task_manager, audio_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.audio_manager = audio_manager

        # TopBar title
        self.top_bar.bar_title.set_text("Select Alarm")


        # Alarm picker partition
        self.saved_alarms_partition = Partition()
        # Alarm picker button as a dropdown
        self.saved_alarms_button = CustomSettingsButton(text="Saved Alarms", width=1, color_state=STATE.ACTIVE)
        self.saved_alarms_button.bind(on_release=lambda instance: self.navigation_manager.navigate_to(SCREEN.SAVED_ALARMS))
        self.saved_alarms_partition.add_widget(self.saved_alarms_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.saved_alarms_partition)

        # Create alarm partition
        self.create_alarm_partition = Partition()
        # Start recording button
        self.start_recording_button = CustomSettingsButton(text="Start Recording", width=1, color_state=STATE.ACTIVE)
        self.start_recording_button.bind(on_release=self.start_recording_alarm)
        self.create_alarm_partition.add_widget(self.start_recording_button)
        # Stop recording button
        self.stop_recording_button = CustomSettingsButton(text="Stop Recording", width=1, color_state=STATE.INACTIVE)
        self.stop_recording_button.bind(on_release=self.stop_recording_alarm)
        self.create_alarm_partition.add_widget(self.stop_recording_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.create_alarm_partition)
        
        # Preview alarm partition
        self.preview_alarm_partition = Partition()
        # Create alarm display box
        self.selected_alarm = SettingsField(text="No alarm selected", width=1, color_state=STATE.INACTIVE)
        self.preview_alarm_partition.add_widget(self.selected_alarm)
        # Selected alarm row
        self.preview_alarm_row = CustomSettingsButtonsRow()
        # Play selected alarm button
        self.play_selected_alarm_button = CustomSettingsButton(text="Play Selected Alarm", width=1, color_state=STATE.INACTIVE)
        self.play_selected_alarm_button.bind(on_release=self.play_selected_alarm)
        self.preview_alarm_row.add_widget(self.play_selected_alarm_button)
        # Stop selected alarm button
        self.stop_selected_alarm_button = CustomSettingsButton(text="Stop Selected Alarm", width=1, color_state=STATE.INACTIVE)
        self.stop_selected_alarm_button.bind(on_release=self.stop_selected_alarm)
        self.preview_alarm_row.add_widget(self.stop_selected_alarm_button)
        # Edit selected alarm button
        self.edit_selected_alarm_button = CustomSettingsButton(text="Edit Selected Alarm", width=1, color_state=STATE.INACTIVE)
        self.edit_selected_alarm_button.bind(on_release=self.edit_selected_alarm_name)
        self.preview_alarm_row.add_widget(self.edit_selected_alarm_button)

        # Add to scroll container
        self.preview_alarm_partition.add_widget(self.preview_alarm_row)
        self.scroll_container.container.add_widget(self.preview_alarm_partition)

        # Vibrating partition
        self.vibration_partition = Partition()
        # Vibrating button
        self.vibration_button = CustomSettingsButton(text="Vibration off", width=1, color_state=STATE.INACTIVE)
        self.vibration_button.bind(on_release=self.toggle_vibration)
        self.vibration_partition.add_widget(self.vibration_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.vibration_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=self.cancel_select_alarm)
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = CustomConfirmButton(text="Select", width=2)
        self.save_button.bind(on_release=self.select_alarm)
        self.button_row.add_widget(self.save_button)
        self.confirmation_partition.add_widget(self.button_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add widget directly to display screen
        self.add_widget(self.root_layout)
    
    def unschedule_audio_check(self):
        """Unschedule the audio finished check."""
        Clock.unschedule(self.check_audio_finished)
    
    def update_playback_button_states(self, is_playing: bool) -> None:
        """
        Update playback button states based on whether audio is playing.
        """
        self.set_button_state(
            self.play_selected_alarm_button, 
            active=not is_playing, 
            enabled=not is_playing
        )
        self.set_button_state(
            self.stop_selected_alarm_button, 
            active=is_playing, 
            enabled=is_playing
        )
        
        # Also disable edit and save buttons while playing
        if is_playing:
            self.set_button_state(
                self.edit_selected_alarm_button,
                active=False,
                enabled=False
            )
            # Disable save button during playback
            self.set_button_state(
                self.save_button,
                active=False,
                enabled=False
            )
        else:
            # Restore edit button state based on alarm selection
            has_alarm = self.audio_manager.selected_alarm_name is not None
            self.set_button_state(
                self.edit_selected_alarm_button,
                active=has_alarm,
                enabled=has_alarm
            )
            # Always enable save button when not playing
            self.set_button_state(
                self.save_button,
                active=True,
                enabled=True
            )
    
    def update_recording_button_states(self, is_recording: bool) -> None:
        """
        Update recording button states based on whether recording is active.
        """
        self.set_button_state(
            self.start_recording_button, 
            active=not is_recording, 
            enabled=not is_recording,
            text="Recording..." if is_recording else "Start Recording"
        )
        self.set_button_state(
            self.stop_recording_button, 
            active=is_recording, 
            enabled=is_recording
        )
    
    def cancel_select_alarm(self, instance) -> None:
        """
        Reset the selected alarm and navigate back to the NewTask screen.
        """
        self.unschedule_audio_check()
        
        self.audio_manager.selected_alarm_name = None
        self.audio_manager.selected_alarm_path = None
        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)

    def update_selected_alarm_text(self) -> None:
        """
        Update the selected alarm text display only.
        """
        if self.audio_manager.is_recording:
            self.selected_alarm.set_text("Recording...")
        elif self.audio_manager.selected_alarm_name is None:
            self.selected_alarm.set_text("No alarm selected")
        else:
            self.selected_alarm.set_text(self.audio_manager.selected_alarm_name)
    
    def update_button_states_based_on_alarm(self) -> None:
        """
        Update button states based on alarm selection and recording state.
        """
        has_alarm = self.audio_manager.selected_alarm_name is not None
        is_playing = self.audio_manager.is_playing()
        
        if self.audio_manager.is_recording:
            # Disable play, stop, edit during recording
            self.set_button_state(self.play_selected_alarm_button, active=False, enabled=False)
            self.set_button_state(self.stop_selected_alarm_button, active=False, enabled=False)
            self.set_button_state(self.edit_selected_alarm_button, active=False, enabled=False)
            # Keep existing logic for save button during recording
            self.set_button_state(self.save_button, active=False, enabled=False)
        elif is_playing:
            # Disable edit and select buttons during playback
            self.set_button_state(self.play_selected_alarm_button, active=False, enabled=False)
            self.set_button_state(self.stop_selected_alarm_button, active=True, enabled=True)
            self.set_button_state(self.edit_selected_alarm_button, active=False, enabled=False)
            self.set_button_state(self.save_button, active=False, enabled=False)
        else:
            # Normal state when not recording or playing
            self.set_button_state(self.play_selected_alarm_button, active=has_alarm, enabled=has_alarm)
            self.set_button_state(self.stop_selected_alarm_button, active=False, enabled=False)
            self.set_button_state(self.edit_selected_alarm_button, active=has_alarm, enabled=has_alarm)
            
            # Always enable save button when not recording or playing
            self.set_button_state(self.save_button, active=True, enabled=True)
    
    def update_screen_state(self) -> None:
        """
        Checks for audio state (playing/recording) and updates UI accordingly.
        """
        self.update_selected_alarm_text()
        self.update_button_states_based_on_alarm()
        
    def start_recording_alarm(self, instance) -> None:
        """Start recording an alarm"""
        was_playing: bool = self.audio_manager.is_playing()
        
        # Prevent play_button from being re-enabled
        self.unschedule_audio_check()
        
        if self.audio_manager.start_recording_audio():
            self.audio_manager.is_recording = True
            self.update_recording_button_states(True)
            self.update_screen_state()

        else:
            self.show_error_popup("Recording Error", "Could not start recording")
            
            # Restore states if recording failed
            if was_playing:
                self.set_button_state(self.play_selected_alarm_button, active=True, enabled=True)

    def stop_recording_alarm(self, instance) -> None:
        """Stop recording an alarm"""
        if self.audio_manager.stop_recording_audio():
            self.audio_manager.is_recording = False
            self.update_recording_button_states(False)
            self.update_screen_state()

        else:
            self.show_error_popup("Recording Error", "Could not stop recording")

    def play_selected_alarm(self, instance) -> None:
        """Play the selected alarm"""
        if not self.audio_manager.selected_alarm_path:
            self.show_error_popup("Playback Error", "No alarm selected")
            return
        
        if self.audio_manager.start_playing_audio():
            self.update_playback_button_states(True)
            
            # Update buttons states when audio finishes
            Clock.schedule_interval(self.check_audio_finished, 0.3)
        else:
            self.show_error_popup("Playback Error", "Could not play the selected alarm")

    def stop_selected_alarm(self, instance) -> None:
        """Stop the currently playing alarm"""
        success: bool = self.audio_manager.stop_playing_audio()
        
        if success:
            self.update_playback_button_states(False)
            # Re-enable the save button when audio stops playing
            self.set_button_state(self.save_button, active=True, enabled=True)
            # Remove scheduled check
            self.unschedule_audio_check()
            return False
        return True

    def check_audio_finished(self, dt: float) -> bool:
        """Check if audio has finished playing and update buttons accordingly"""
        if not self.audio_manager.is_playing():
            self.update_playback_button_states(False)
            # Remove scheduled check
            self.unschedule_audio_check()
            return False
        return True

    def edit_selected_alarm_name(self, instance) -> None:
        """Edit the name of the selected alarm"""
        pass

    def toggle_vibration(self, instance) -> None:
        """Toggle vibration on the selected alarm"""
        self.task_manager.vibrate = not self.task_manager.vibrate
        self.set_button_state(
            self.vibration_button,
            active=self.task_manager.vibrate,
            text="Vibrating on" if self.task_manager.vibrate else "Vibration off"
        )

    def select_alarm(self, instance) -> None:
        """Select the alarm and return to previous screen"""
        # Remove scheduled checks
        self.unschedule_audio_check()
        
        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)

    def on_pre_enter(self) -> None:
        """Called when the screen is entered"""
        super().on_pre_enter()
        
        self.update_screen_state()
        self.set_button_state(
            self.stop_selected_alarm_button, 
            active=False, 
            enabled=False
        )

    def on_leave(self) -> None:
        """Called when the screen is left"""
        super().on_leave()
        # Stop any playing audio and remove scheduled checks
        self.audio_manager.stop_playing_audio()
        self.unschedule_audio_check()
 