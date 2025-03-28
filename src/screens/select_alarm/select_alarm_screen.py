import os

from kivy.core.audio import SoundLoader
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from src.screens.base.base_screen import BaseScreen

from src.utils.bars import TopBarClosed, TopBarExpanded
from src.utils.containers import BaseLayout, ScrollContainer, Partition, CustomButtonRow
from src.utils.buttons import CustomButton, CustomSettingsButton
from src.utils.fields import SettingsField

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
        self.saved_alarms_button.bind(on_press=lambda instance: self.navigation_manager.navigate_to(SCREEN.SAVED_ALARMS))
        self.saved_alarms_partition.add_widget(self.saved_alarms_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.saved_alarms_partition)

        # Create alarm partition
        self.create_alarm_partition = Partition()
        # Start recording button
        self.start_recording_button = CustomSettingsButton(text="Start Recording", width=1, color_state=STATE.ACTIVE)
        self.start_recording_button.bind(on_press=self.start_recording)
        self.create_alarm_partition.add_widget(self.start_recording_button)
        # Stop recording button
        self.stop_recording_button = CustomSettingsButton(text="Stop Recording", width=1, color_state=STATE.INACTIVE)
        self.stop_recording_button.bind(on_press=self.stop_recording)
        self.create_alarm_partition.add_widget(self.stop_recording_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.create_alarm_partition)
        
        # Preview alarm partition
        self.preview_alarm_partition = Partition()
        # Create alarm display box
        self.selected_alarm = SettingsField(text="No alarm selected", width=1, color_state=STATE.INACTIVE)
        self.preview_alarm_partition.add_widget(self.selected_alarm)
        # Play selected alarm button
        self.play_selected_alarm_button = CustomSettingsButton(text="Play Selected Alarm", width=1, color_state=STATE.INACTIVE)
        self.play_selected_alarm_button.bind(on_press=self.play_selected_alarm)
        self.preview_alarm_partition.add_widget(self.play_selected_alarm_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.preview_alarm_partition)

        # Vibrating partition
        self.vibration_partition = Partition()
        # Vibrating button
        self.vibration_button = CustomSettingsButton(text="Vibration off", width=1, color_state=STATE.INACTIVE)
        self.vibration_button.bind(on_press=self.toggle_vibration)
        self.vibration_partition.add_widget(self.vibration_button)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.vibration_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomButton(text="Cancel", width=2, color_state=STATE.INACTIVE)
        self.cancel_button.bind(on_press=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK))
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = CustomButton(text="Select", width=2, color_state=STATE.ACTIVE)
        self.save_button.bind(on_press=self.select_alarm)
        self.button_row.add_widget(self.save_button)
        self.confirmation_partition.add_widget(self.button_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

    def update_selected_alarm_text(self):
        """Update the selected alarm text"""
        if self.recording_on:
            self.selected_alarm.set_text("Recording...")
            self.play_selected_alarm_button.set_inactive_state()

        elif self.audio_manager.selected_alarm_name is None:
            self.selected_alarm.set_text("No alarm selected")
            self.play_selected_alarm_button.set_inactive_state()

        else:
            self.selected_alarm.set_text(self.audio_manager.selected_alarm_name)
            self.play_selected_alarm_button.set_active_state()
            
    def start_recording(self, instance):
        """Start recording an alarm"""
        if self.audio_manager.start_recording():
            # Update UI
            self.recording_on = True
            self.start_recording_button.set_text("Recording...")
            self.start_recording_button.set_inactive_state()
            self.stop_recording_button.set_active_state()
            self.update_selected_alarm_text()
        else:
            # Show error popup
            popup = Popup(title="Recording Error",
                        content=Label(text="Could not start recording"),
                        size_hint=(0.8, 0.4))
            popup.open()

    def stop_recording(self, instance):
        """Stop recording an alarm"""
        if self.audio_manager.stop_recording():
            # Update UI
            self.recording_on = False
            self.start_recording_button.set_text("Start Recording")
            self.start_recording_button.set_active_state()
            self.stop_recording_button.set_inactive_state()
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
        
        if not os.path.exists(self.audio_manager.selected_alarm_path):
            popup = Popup(title="Playback Error",
                        content=Label(text=f"Alarm file not found: {self.audio_manager.selected_alarm_path.split('/')[-3:]}"),
                        size_hint=(0.8, 0.4))
            popup.open()
            return
        
        if self.audio_manager.is_android():
            try:
                from jnius import autoclass  # type: ignore
                MediaPlayer = autoclass('android.media.MediaPlayer')
                
                # Create and store a reference to the player to prevent garbage collection
                self._current_player = MediaPlayer()
                self._current_player.setDataSource(self.audio_manager.selected_alarm_path)
                self._current_player.prepare()
                self._current_player.start()
                return
            except Exception as e:
                raise e

        # Non-Android platforms        
        try:
            sound = SoundLoader.load(self.audio_manager.selected_alarm_path)
            if sound:
                sound.play()
            else:
                popup = Popup(
                        title="Playback Error",
                        content=Label(
                            text=f"Could not load sound: {self.audio_manager.selected_alarm_path}",
                            size_hint_y=None,
                            text_size=(None, None),
                            halign="left",
                            valign="top"
                        ),
                        size_hint=(0.8, 0.4)
                    )
                popup.content.bind(size=popup.content.setter('text_size'))
                popup.open()
        except Exception as e:
            raise e

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
        """Save the selected alarm"""
        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)

    def on_pre_enter(self):
        """Called when the screen is entered"""
        super().on_pre_enter()
        self.update_selected_alarm_text()
    