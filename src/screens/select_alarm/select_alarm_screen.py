import os

from kivy.core.audio import SoundLoader
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from src.screens.base.base_screen import BaseScreen

from src.widgets.bars import TopBarClosed, TopBarExpanded
from src.widgets.containers import BaseLayout, ScrollContainer, Partition, CustomButtonRow, CustomSettingsButtonsRow
from src.widgets.buttons import CustomConfirmButton, CustomSettingsButton, CustomCancelButton
from src.widgets.fields import SettingsField

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

        self.recording_on = False
        self.vibration_on = False

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = TopBarClosed(
            bar_title="Select Alarm",
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK),
            options_callback=lambda instance: self.switch_top_bar(),
        )
        # Top bar with expanded options
        self.top_bar_expanded = TopBarExpanded(
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK),
            screenshot_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.START),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=lambda instance: self.navigation_manager.exit_app(),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

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

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
    
    def cancel_select_alarm(self, instance):
        """Cancel the select alarm process"""
        # Unschedule any check
        from kivy.clock import Clock
        Clock.unschedule(self.check_audio_finished)
        
        self.audio_manager.selected_alarm_name = None
        self.audio_manager.selected_alarm_path = None
        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)

    def update_selected_alarm_text(self):
        """Update the selected alarm text and save button state"""
        if self.recording_on:
            self.selected_alarm.set_text("Recording...")
            self.play_selected_alarm_button.set_inactive_state()
            self.play_selected_alarm_button.set_disabled(True)
            self.stop_selected_alarm_button.set_disabled(True)
            self.save_button.set_inactive_state()  # Can't save while recording
            self.save_button.set_disabled(True)

        elif self.audio_manager.selected_alarm_name is None:
            self.selected_alarm.set_text("No alarm selected")
            self.play_selected_alarm_button.set_inactive_state()
            self.play_selected_alarm_button.set_disabled(True)
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)
            self.save_button.set_inactive_state()  # No alarm selected = inactive save button
            self.save_button.set_disabled(True)

        else:
            self.selected_alarm.set_text(self.audio_manager.selected_alarm_name)
            self.play_selected_alarm_button.set_active_state()
            self.play_selected_alarm_button.set_disabled(False)
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)
            self.save_button.set_active_state()  # Alarm selected = active save button
            self.save_button.set_disabled(False)
            
    def start_recording_alarm(self, instance):
        """Start recording an alarm"""
        was_playing = self.audio_manager.is_playing()
        
        # We need to unschedule the check that would otherwise
        # automatically re-enable the play button
        from kivy.clock import Clock
        Clock.unschedule(self.check_audio_finished)
        
        if self.audio_manager.start_recording_audio():
            # Update UI
            self.recording_on = True
            self.start_recording_button.set_text("Recording...")
            self.start_recording_button.set_inactive_state()
            self.start_recording_button.set_disabled(True)
            
            self.stop_recording_button.set_active_state()
            self.stop_recording_button.set_disabled(False)
            
            # Always disable play/stop buttons during recording
            # regardless of what happened before
            self.play_selected_alarm_button.set_inactive_state()
            self.play_selected_alarm_button.set_disabled(True)
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)
            
            self.update_selected_alarm_text()
        else:
            # Show error popup
            popup = Popup(title="Recording Error",
                         content=Label(text="Could not start recording"),
                         size_hint=(0.8, 0.4))
            popup.open()
            
            # If recording failed but we stopped playback, restore buttons to non-recording state
            if was_playing:
                self.play_selected_alarm_button.set_active_state()
                self.play_selected_alarm_button.set_disabled(False)

    def stop_recording_alarm(self, instance):
        """Stop recording an alarm"""
        if self.audio_manager.stop_recording_audio():
            # Update UI
            self.recording_on = False
            self.start_recording_button.set_text("Start Recording")
            self.start_recording_button.set_active_state()
            self.start_recording_button.set_disabled(False)
            
            self.stop_recording_button.set_inactive_state()
            self.stop_recording_button.set_disabled(True)
            
            self.update_selected_alarm_text()
        else:
            # Show error popup
            popup = Popup(title="Recording Error",
                        content=Label(text="Could not stop recording"),
                        size_hint=(0.8, 0.4))
            popup.open()

    def play_selected_alarm(self, instance):
        """Play the selected alarm"""
        if not self.audio_manager.selected_alarm_path:
            popup = Popup(title="Playback Error",
                        content=Label(text="No alarm selected"),
                        size_hint=(0.8, 0.4))
            popup.open()
            return
        
        if self.audio_manager.start_playing_audio():
            # Update button states
            self.play_selected_alarm_button.set_inactive_state()
            self.play_selected_alarm_button.set_disabled(True)
            
            self.stop_selected_alarm_button.set_active_state()
            self.stop_selected_alarm_button.set_disabled(False)
            
            # Schedule a check to update buttons when audio finishes
            from kivy.clock import Clock
            Clock.schedule_interval(self.check_audio_finished, 0.3)
        else:
            # Show error popup
            popup = Popup(
                    title="Playback Error",
                    content=Label(
                        text="Could not play the selected alarm",
                        size_hint_y=None,
                        text_size=(None, None),
                        halign="left",
                        valign="top"
                    ),
                    size_hint=(0.8, 0.4)
                )
            popup.content.bind(size=popup.content.setter('text_size'))
            popup.open()

    def stop_selected_alarm(self, instance):
        """Stop the currently playing alarm"""
        success = self.audio_manager.stop_playing_audio()
        
        if success:
            # Update button states
            self.play_selected_alarm_button.set_active_state()
            self.play_selected_alarm_button.set_disabled(False)
            
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)
            
            # Unschedule the check
            from kivy.clock import Clock
            Clock.unschedule(self.check_audio_finished)
        else:
            # Show error popup
            popup = Popup(
                    title="Playback Error",
                    content=Label(text="Could not stop the alarm playback"),
                    size_hint=(0.8, 0.4)
                )
            popup.open()

    def check_audio_finished(self, dt):
        """Check if audio has finished playing and update buttons accordingly"""
        if not self.audio_manager.is_playing():
            # Audio finished playing, update button states
            self.play_selected_alarm_button.set_active_state()
            self.play_selected_alarm_button.set_disabled(False)
            
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)
            
            # Unschedule this check
            from kivy.clock import Clock
            Clock.unschedule(self.check_audio_finished)
            return False
        return True

    def edit_selected_alarm_name(self, instance):
        """Edit the name of the selected alarm"""
        # Implement this based on your requirements
        pass

    def toggle_vibration(self, instance):
        """Toggle vibration on the selected alarm"""
        self.vibration_on = not self.vibration_on
        if self.vibration_on:
            self.vibration_button.set_text("Vibrating on")
            self.vibration_button.set_active_state() 
        else:
            self.vibration_button.set_text("Vibration off")
            self.vibration_button.set_inactive_state()

    def select_alarm(self, instance):
        """Select the alarm and return to previous screen"""
        # Unschedule any check
        from kivy.clock import Clock
        Clock.unschedule(self.check_audio_finished)
        
        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)

    def on_pre_enter(self):
        """Called when the screen is entered"""
        super().on_pre_enter()
        self.update_selected_alarm_text()  # This will also update the save button
        
        # Make sure buttons are in the correct state
        if self.audio_manager.is_playing():
            # If audio is already playing when entering the screen
            self.play_selected_alarm_button.set_inactive_state()
            self.play_selected_alarm_button.set_disabled(True)
            self.stop_selected_alarm_button.set_active_state()
            self.stop_selected_alarm_button.set_disabled(False)
            
            # Schedule check for when audio finishes
            from kivy.clock import Clock
            Clock.schedule_interval(self.check_audio_finished, 0.5)
        else:
            # Normal state - play enabled, stop disabled
            self.stop_selected_alarm_button.set_inactive_state()
            self.stop_selected_alarm_button.set_disabled(True)

    def on_leave(self):
        """Called when the screen is left"""
        super().on_leave()
        # Make sure we stop any playing audio and unschedule checks
        self.audio_manager.stop_playing_audio(log=False)
        from kivy.clock import Clock
        Clock.unschedule(self.check_audio_finished)
 