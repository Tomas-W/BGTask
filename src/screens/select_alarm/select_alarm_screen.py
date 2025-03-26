import os
import sys
from datetime import datetime

from kivy.core.audio import SoundLoader
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen

from src.utils.bars import TopBarClosed, TopBarExpanded
from src.utils.containers import BaseLayout, ScrollContainer, Partition, CustomButtonRow
from src.utils.buttons import CustomButton, CustomSettingsButton
from src.utils.fields import SettingsField

from src.settings import STATE, PATH

# Add this function to check if we're on Android
def is_android():
    """Check if the app is running on Android"""
    return hasattr(sys, "getandroidapilevel")

class SelectAlarmScreen(BaseScreen):
    """
    Screen for selecting an alarm.
    """
    def __init__(self, navigation_manager, task_manager, alarm_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.alarm_manager = alarm_manager

        self.recording_on = False
        self.vibration_on = False

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = TopBarClosed(
            bar_title="Select Alarm",
            back_callback=lambda instance: self.navigation_manager.go_back(instance=instance),
            options_callback=self.switch_top_bar,
        )
        # Top bar with expanded options
        self.top_bar_expanded = TopBarExpanded(
            back_callback=lambda instance: self.navigation_manager.go_back(instance=instance),
            options_callback=self.switch_top_bar,
            settings_callback=lambda instance: self.navigation_manager.go_to_settings_screen(instance=instance),
            exit_callback=lambda instance: self.navigation_manager.exit_app(instance=instance),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Alarm picker partition
        self.saved_alarms_partition = Partition()
        # Alarm picker button as a dropdown
        self.saved_alarms_button = CustomSettingsButton(text="Saved Alarms", width=1, color_state=STATE.ACTIVE)
        self.saved_alarms_button.bind(on_press=self.navigation_manager.go_to_saved_alarms_screen)
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
        self.cancel_button.bind(on_press=lambda instance: self.navigation_manager.go_to_new_task_screen())
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = CustomButton(text="Select", width=2, color_state=STATE.ACTIVE)
        self.save_button.bind(on_press=self.save_alarm)
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

        elif self.alarm_manager.selected_alarm_name is None:
            self.selected_alarm.set_text("No alarm selected")
            self.play_selected_alarm_button.set_inactive_state()

        else:
            self.selected_alarm.set_text(self.alarm_manager.selected_alarm_name)
            self.play_selected_alarm_button.set_active_state()

    def request_android_permissions(self):
        """Request necessary Android permissions"""
        if is_android():
            try:
                from android.permissions import request_permissions, Permission
                from kivy.clock import Clock
                
                def callback(permissions, results):
                    if all(results):
                        print("All permissions granted.")
                        # Successfully got permissions, can proceed
                    else:
                        print("Some permissions not granted.")
                        # Use Clock to schedule the popup on the main thread
                        Clock.schedule_once(lambda dt: self.show_permission_error(), 0)
                
                request_permissions([
                    Permission.RECORD_AUDIO,
                    Permission.WRITE_EXTERNAL_STORAGE, 
                    Permission.READ_EXTERNAL_STORAGE
                ], callback)
            except Exception as e:
                print(f"Error requesting permissions: {e}")

    def show_permission_error(self):
        """Show permission error popup (called on main thread)"""
        popup = Popup(title="Permission Error",
                    content=Label(text="Audio recording requires microphone permission"),
                    size_hint=(0.8, 0.4))
        popup.open()

    def ensure_directory_exists(self, directory):
        """Make sure a directory exists, creating it if necessary"""
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                return True
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return False
        return True

    def get_recording_path(self):
        """Get a valid path for recording based on platform"""
        filename = f"recording{datetime.now().strftime('_%H-%M-%S')}"
        
        if is_android():
            # Use the AlarmManager's storage path for consistency
            alarms_dir = self.alarm_manager.storage_path
            if self.ensure_directory_exists(alarms_dir):
                extension = ".mp3"  # Change from .3gp to .mp3 for better compatibility
                path = os.path.join(alarms_dir, filename + extension)
                return filename, path, extension
        else:
            # Use the AlarmManager's storage path for consistency
            if self.ensure_directory_exists(self.alarm_manager.storage_path):
                extension = ".wav"
                path = os.path.join(self.alarm_manager.storage_path, filename + extension)
                return filename, path, extension
            
        # Last resort if no directory can be created
        import tempfile
        temp_dir = tempfile.gettempdir()
        extension = ".wav"
        path = os.path.join(temp_dir, filename + extension)
        return filename, path, extension

    def start_recording(self, instance):
        """Start recording an alarm"""
        # Request permissions if on Android
        if is_android():
            from android.permissions import check_permission, Permission
            
            # Check if we already have permissions before requesting
            if not check_permission(Permission.RECORD_AUDIO):
                # Request permissions first, then try recording when granted
                self.request_android_permissions()
                # Show a message to the user
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: Popup(
                    title="Permission Required", 
                    content=Label(text="Please grant microphone permission to record"),
                    size_hint=(0.8, 0.4)).open(), 0)
                return
        
        # Get appropriate recording path
        filename, path, extension = self.get_recording_path()
        
        try:
            if is_android():
                # Configure a new MediaRecorder instance with reliable settings
                try:
                    from jnius import autoclass
                    MediaRecorder = autoclass('android.media.MediaRecorder')
                    AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
                    OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
                    AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
                    
                    # Create a fresh recorder each time
                    recorder = MediaRecorder()
                    recorder.setAudioSource(AudioSource.MIC)
                    
                    # For mp3 format:
                    if extension.lower() == '.mp3':
                        recorder.setOutputFormat(OutputFormat.MPEG_4)
                        recorder.setAudioEncoder(AudioEncoder.AAC)
                    else:
                        # Default to 3GP
                        recorder.setOutputFormat(OutputFormat.THREE_GPP)
                        recorder.setAudioEncoder(AudioEncoder.AMR_NB)
                        
                    recorder.setOutputFile(path)
                    recorder.prepare()
                    recorder.start()
                    
                    # Store the recorder for later stopping
                    self.alarm_manager.android_recorder = recorder
                    
                    # Successfully started recording
                    self.recording_on = True
                    self.alarm_manager.selected_alarm_name = filename
                    self.alarm_manager.selected_alarm_path = path
                    
                    # Update UI
                    self.start_recording_button.set_text("Recording...")
                    self.start_recording_button.set_inactive_state()
                    self.stop_recording_button.set_active_state()
                    self.update_selected_alarm_text()
                    return
                except Exception as e:
                    print(f"Error with direct Android recording: {e}")
                
                # Fallback to Plyer if direct approach failed
                self.alarm_manager.plyer_audio.file_path = path
            
            # Try Plyer approach (for non-Android or as fallback)
            self.alarm_manager.plyer_audio.start()
            self.recording_on = True
            self.alarm_manager.selected_alarm_name = filename
            self.alarm_manager.selected_alarm_path = path
            
            # Update UI
            self.start_recording_button.set_text("Recording...")
            self.start_recording_button.set_inactive_state()
            self.stop_recording_button.set_active_state()
            self.update_selected_alarm_text()
            
        except Exception as e:
            error_msg = f"Could not start recording: {str(e)}"
            print(error_msg)
            
            # Show error to user with Clock to ensure it's on the main thread
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: Popup(
                title="Recording Error",
                content=Label(text=error_msg),
                size_hint=(0.8, 0.4)).open(), 0)
            
            self.recording_on = False

    def stop_recording(self, instance):
        """Stop recording an alarm"""
        try:
            # Try to stop the direct Android recorder if it exists
            if is_android() and hasattr(self.alarm_manager, 'android_recorder'):
                try:
                    self.alarm_manager.android_recorder.stop()
                    self.alarm_manager.android_recorder.release()
                    delattr(self.alarm_manager, 'android_recorder')
                except Exception as e:
                    print(f"Error stopping Android recorder: {e}")
            else:
                # Use Plyer approach
                self.alarm_manager.plyer_audio.stop()
        except Exception as e:
            print(f"Error stopping recording: {e}")
            # Show error using Clock to run on main thread
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: Popup(
                title="Recording Error",
                content=Label(text=f"Error stopping recording: {str(e)}"),
                size_hint=(0.8, 0.4)).open(), 0)
        
        self.recording_on = False
        self.start_recording_button.set_text("Start Recording")
        self.start_recording_button.set_active_state()
        self.stop_recording_button.set_inactive_state()

        self.update_selected_alarm_text()

    def play_selected_alarm(self, instance):
        """Play the selected alarm"""
        if not self.alarm_manager.selected_alarm_path:
            popup = Popup(title="Playback Error",
                        content=Label(text="No alarm selected"),
                        size_hint=(0.8, 0.4))
            popup.open()
            return
        
        if not os.path.exists(self.alarm_manager.selected_alarm_path):
            popup = Popup(title="Playback Error",
                        content=Label(text=f"Alarm file not found: {self.alarm_manager.selected_alarm_path}"),
                        size_hint=(0.8, 0.4))
            popup.open()
            return
        
        # For Android, use the MediaPlayer directly
        if is_android():
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                
                # Create and store a reference to the player to prevent garbage collection
                self._current_player = MediaPlayer()
                self._current_player.setDataSource(self.alarm_manager.selected_alarm_path)
                self._current_player.prepare()
                self._current_player.start()
                return
            except Exception as e:
                # Log the error but continue to try with SoundLoader as fallback
                print(f"Error using Android MediaPlayer: {e}")
        
        # For non-Android platforms or as a fallback, use SoundLoader
        try:
            sound = SoundLoader.load(self.alarm_manager.selected_alarm_path)
            if sound:
                sound.play()
            else:
                popup = Popup(
                        title="Playback Error",
                        content=Label(
                            text=f"Could not load sound: {self.alarm_manager.selected_alarm_path}",
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
            popup = Popup(
                    title="Playback Error",
                    content=Label(
                        text=f"Error playing sound: {str(e)}",
                        size_hint_y=None,
                        text_size=(None, None),
                        halign="left",
                        valign="top"
                    ),
                    size_hint=(0.8, 0.4)
                )
            popup.content.bind(size=popup.content.setter('text_size'))
            popup.open()

    def toggle_vibration(self, instance):
        """Toggle vibration on the selected alarm"""
        self.vibration_on = not self.vibration_on
        if self.vibration_on:
            self.vibration_button.set_text("Vibrating on")
            self.vibration_button.set_active_state() 
        else:
            self.vibration_button.set_text("Vibration off")
            self.vibration_button.set_inactive_state()

    def save_alarm(self, instance):
        """Save the selected alarm"""
        self.navigation_manager.go_to_new_task_screen()

    def on_pre_enter(self):
        """Called when the screen is entered"""
        super().on_pre_enter()
        self.update_selected_alarm_text()



