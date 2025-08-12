import json

from typing import TYPE_CHECKING
from kivy.clock import Clock

from src.screens.base.base_screen import BaseScreen
from src.widgets.containers import CustomButtonRow, Partition
from src.widgets.buttons import ConfirmButton, SettingsButton, SettingsConfirmButton
from src.widgets.fields import SettingsField

from managers.popups.popup_manager import POPUP
from managers.device.device_manager import DM

from src.utils.logger import logger
from src.settings import SPACE, STATE

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_task_manager import TaskManager
    from src.app_managers.app_audio_manager import AudioManager
    from src.app_managers.app_communication_manager import AppCommunicationManager


class NewTargetScreen(BaseScreen):
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager
        self.audio_manager: "AudioManager" = app.audio_manager
        self.communication_manager: "AppCommunicationManager" = app.communication_manager

        self.preset_name: str | None = None
        self.target_name: str | None = None
        self.alert_distance: int | None = None
        self.targets: list[float] = []
        self.alarm_name: str | None = None

        self.top_bar.bar_title.set_text("New Target")
        self.scroll_container.container.spacing = SPACE.SPACE_M

        self.presets_partition = Partition()
        self.presets_partition.spacing = SPACE.SPACE_XS
        # Select
        self.select_preset_button = SettingsConfirmButton(text="Select Preset", width=1, color_state=STATE.ACTIVE)
        self.select_preset_button.bind(on_release=self._show_select_preset_popup)
        self.presets_partition.add_widget(self.select_preset_button)
        # Save
        self.save_preset_button = SettingsConfirmButton(text="Save Preset", width=1, color_state=STATE.INACTIVE)
        self.save_preset_button.bind(on_release=self._save_preset)
        self.presets_partition.add_widget(self.save_preset_button)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.presets_partition)

        self.target_name_partition = Partition()
        self.target_name_partition.spacing = SPACE.SPACE_XS
        # Select
        self.target_name_button = SettingsButton(text="Name", width=1, color_state=STATE.ACTIVE)
        self.target_name_button.bind(on_release=self._show_select_target_name_popup)
        self.target_name_partition.add_widget(self.target_name_button)
        # Display
        self.target_name_field = SettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.target_name_partition.add_widget(self.target_name_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.target_name_partition)

        self.alert_distance_partition = Partition()
        self.alert_distance_partition.spacing = SPACE.SPACE_XS
        # Select
        self.alert_distance_button = SettingsButton(text="Alert Distance", width=1, color_state=STATE.ACTIVE)
        self.alert_distance_button.bind(on_release=self._show_select_alert_distance_popup)
        self.alert_distance_partition.add_widget(self.alert_distance_button)
        # Display
        self.alert_distance_field = SettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.alert_distance_partition.add_widget(self.alert_distance_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.alert_distance_partition)

        self.target_partition = Partition()
        self.target_partition.spacing = SPACE.SPACE_XS
        # Select
        self.select_target_button = SettingsButton(text="Select Target", width=1, color_state=STATE.ACTIVE)
        self.select_target_button.bind(on_release=self.navigate_to_map_screen)
        self.target_partition.add_widget(self.select_target_button)
        # Display
        self.target_field = SettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.target_partition.add_widget(self.target_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.target_partition)

        self.alarm_partition = Partition()
        self.alarm_partition.spacing = SPACE.SPACE_XS
        # Select
        self.select_alarm_button = SettingsButton(text="Select Alarm", width=1, color_state=STATE.ACTIVE)
        self.select_alarm_button.bind(on_release=self._show_saved_alarms_popup)
        self.alarm_partition.add_widget(self.select_alarm_button)
        # Display
        self.alarm_field = SettingsField(text="", width=1, color_state=STATE.INACTIVE)
        self.alarm_partition.add_widget(self.alarm_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.alarm_partition)

        self.confirm_partition = Partition()
        self.confirm_partition.spacing = SPACE.SPACE_XS
        self.button_row = CustomButtonRow()
        # Cancel
        self.cancel_button = ConfirmButton(text="Cancel", width=2, color_state=STATE.ACTIVE)
        self.cancel_button.bind(on_release=self._cancel_tracking_target)
        self.button_row.add_widget(self.cancel_button)
        # Confirm
        self.confirm_button = ConfirmButton(text="Track", width=2, color_state=STATE.INACTIVE)
        self.confirm_button.bind(on_release=self._start_tracking_target)
        self.button_row.add_widget(self.confirm_button)
        # Add to Partition
        self.confirm_partition.add_widget(self.button_row)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.confirm_partition)

    def on_pre_enter(self) -> None:
        super().on_pre_enter()

        self.update_target_field()
        self.update_button_states()
    
    def on_enter(self) -> None:
        super().on_enter()
        Clock.schedule_once(self._validate_map_screen, 0.05)
    
    def on_leave(self) -> None:
        super().on_leave()
    
    def _show_select_preset_popup(self, instance) -> None:
        POPUP.show_selection_popup(
            header="Select preset",
            current_selection=self.preset_name,
            on_confirm=lambda preset_name: self._select_preset(preset_name),
            on_cancel=None,
            options_list=self._get_preset_names()
        )

    def _get_preset_names(self) -> list[str]:
        """Get the names of the presets"""
        with open(DM.PATH.TARGET_PRESET_FILE, "r") as f:
            data = json.load(f)
            return list(data.keys())
    
    def _select_preset(self, preset_name: str) -> None:
        """Select the preset and return to NewTargetScreen"""
        self.preset_name = preset_name
        data = self._get_preset_data(preset_name)
        logger.error(f"Data: {data}")
        if data:
            self.target_name = preset_name
            self.target_name_field.set_text(self.target_name)
            self.alert_distance = data["alert_distance"]
            self.alert_distance_field.set_text(f"{self.alert_distance:,}m")
            self.targets = data["targets"]
            self.update_target_field()
            self.alarm_name = data["alarm_name"]
            self.alarm_field.set_text(self.alarm_name)
            
        self.update_button_states()
    
    def _get_preset_data(self, preset_name: str) -> dict:
        """Get the data of the preset"""
        try:
            with open(DM.PATH.TARGET_PRESET_FILE, "r") as f:
                data = json.load(f)
        
        except Exception as e:
            logger.error(f"Error getting preset data: {e}")
            return None
        
        preset_data = data.get(preset_name)
        if preset_data:
            return preset_data
        
        logger.error(f"Preset {preset_name} not found")
        return None

    def _save_preset(self, instance) -> None:
        logger.info(f"Saving preset: {self.target_name}")
        if self.target_name in self._get_preset_names():
            self._show_target_name_taken_popup(self.target_name)
            return
        
        if all([self.target_name, self.alert_distance, self.targets, self.alarm_name]):
            new_preset = {
                    "alert_distance": self.alert_distance,
                    "targets": self.targets,
                    "alarm_name": self.alarm_name
            }
            try:
                with open(DM.PATH.TARGET_PRESET_FILE, "r") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading preset file: {e}")
                data = {}
            
            data[self.target_name] = new_preset
            with open(DM.PATH.TARGET_PRESET_FILE, "w") as f:
                json.dump(data, f, indent=4)
            
            self.preset_name = self.target_name
            self.update_button_states()
            self.update_target_field()

    def navigate_to_map_screen(self, *args) -> None:
        """
        Navigates to the MapScreen.
        """
        self.navigation_manager.navigate_to(DM.SCREEN.MAP)
    
    def _validate_map_screen(self, *args) -> bool:
        """Validate the MapScreen"""
        if not DM.LOADED.MAP_SCREEN:
            logger.error("MapScreen not ready - cannot navigate to it")
            return False
        
        if not DM.INITIALIZED.MAP_SCREEN:
            map_screen = self.app.screens.get(DM.SCREEN.MAP)
            map_screen._init_map_content()
        
        return True

    def _show_select_target_name_popup(self, instance) -> None:
        POPUP.show_input_popup(
            header="Provide name",
            input_text=self.target_name,
            on_confirm=lambda input_text: self.validate_target_name(input_text),
            on_cancel=lambda: None
        )
    
    def _show_target_name_taken_popup(self, name: str) -> None:
        POPUP.show_input_popup(
            header="Name already taken",
            input_text=name,
            on_confirm=lambda input_text: self.validate_target_name(input_text),
            on_cancel=lambda: None
        )
    
    def _show_invalid_target_name_popup(self, name: str) -> None:
        POPUP.show_input_popup(
            header="Invalid input",
            input_text=name,
            on_confirm=lambda input_text: self.validate_target_name(input_text),
            on_cancel=lambda: None
        )

    def _show_select_alert_distance_popup(self, instance) -> None:
        POPUP.show_input_popup(
            header="Provide distance in meters",
            input_text=str(self.alert_distance),
            on_confirm=lambda input_text: self.validate_alert_distance(input_text),
            on_cancel=lambda: None
        )
    
    def _show_invalid_target_distance_popup(self, distance: str) -> None:
        POPUP.show_input_popup(
            header="Invalid input",
            input_text=distance,
            on_confirm=lambda input_text: self.validate_alert_distance(input_text),
            on_cancel=lambda: None
        )
    
    def _show_saved_alarms_popup(self, instance=None) -> None:
        """Show a popup with the saved alarms"""
        POPUP.show_selection_popup(
            header="Select alarm",
            current_selection=self.alarm_name,
            on_confirm=lambda alarm_name: self._select_alarm(alarm_name),
            on_cancel=None,
            options_list=list(self.audio_manager.alarms.keys())
        )
    
    def _select_alarm(self, alarm_name: str) -> None:
        """Select the alarm and return to NewTargetScreen"""
        self.alarm_name = alarm_name
        self.alarm_field.set_text(alarm_name)
        self.update_button_states()

    def _start_tracking_target(self, instance) -> None:
        logger.info(f"Starting GPS monitoring:")
        logger.info(f"Target name: {self.target_name}")
        logger.info(f"Alert distance: {self.alert_distance}")
        logger.info(f"Targets: {self.targets}")
        logger.info(f"Alarm name: {self.alarm_name}")

        try:
            with open(DM.PATH.GPS_FILE, "w") as f:
                data = {
                    "name": self.target_name,
                    "alert_distance": self.alert_distance,
                    "targets": self.targets,
                    "alarm_name": self.alarm_name
                }
                json.dump(data, f, indent=4)

                self.communication_manager.send_gps_monitoring_action()
        
        except Exception as e:
            logger.error(f"Error saving target: {e}")

        # Send GPS monitoring request to service with selected coordinates
        # lat, lon = self.targets[0]
        # logger.info(f"Starting GPS monitoring for coordinates: {lat}, {lon}")
        # self.communication_manager.send_gps_monitoring_action(lat, lon)

        # temp_name = "Tankstations"
        # temp_distance = DM.SETTINGS.DEFAULT_ALERT_DISTANCE
        # coordinates = self.coordinates
        # coordinates.append((self.selected_lat, self.selected_lon))
        # self.communication_manager.send_gps_monitoring_action(temp_name, temp_distance, coordinates)

    def _cancel_tracking_target(self, instance) -> None:
        self._reset_fields()
        self.navigation_manager.navigate_back_to(DM.SCREEN.HOME)

    def validate_target_name(self, name: str) -> None:
        """
        Saves the target name if it is valid, prompts for re-try otherwise.
        """
        if len(name.strip()) < DM.SETTINGS.TARGET_NAME_MIN_LENGTH:
            Clock.schedule_once(lambda dt: self._show_invalid_target_name_popup(name), 0.35)
            return
        
        if self._is_target_name_taken(name):
            Clock.schedule_once(lambda dt: self._show_target_name_taken_popup(name), 0.35)
            return
        
        self.target_name = str(name)
        self.target_name_field.set_text(self.target_name)
        self.update_button_states()
        return

    def _is_target_name_taken(self, name: str) -> bool:
        """Return True if the target name is taken, False otherwise"""
        if name in self._get_preset_names():
            return True
        
        return False
    
    def validate_alert_distance(self, distance: str) -> None:
        """
        Saves the alert distance if it is valid, prompts for re-try otherwise.
        """
        if not distance.strip():
            Clock.schedule_once(lambda dt: self._show_invalid_target_distance_popup(distance), 0.35)
            return
        
        try:
            distance = int(distance.strip())
        except ValueError:
            Clock.schedule_once(lambda dt: self._show_invalid_target_distance_popup(distance), 0.35)
            return
        
        if distance < DM.SETTINGS.TARGET_MIN_DISTANCE:
            Clock.schedule_once(lambda dt: self._show_invalid_target_distance_popup(distance), 0.35)
            return
        
        self.alert_distance = int(distance)
        self.alert_distance_field.set_text(f"{distance:,}m")
        self.update_button_states()
    
    def update_target_field(self) -> None:
        if self.targets:
            if len(self.targets) == 1:
                self.target_field.set_text(f"{len(self.targets)//2} target")
            else:
                self.target_field.set_text(f"{len(self.targets)//2} targets")
    
    def update_button_states(self) -> None:
        if all([
            self.target_name,
            self.alert_distance,
            self.targets,
            self.alarm_name
        ]):
            self.confirm_button.set_active_state()
            self.save_preset_button.set_active_state()
        else:
            self.confirm_button.set_inactive_state()
            self.save_preset_button.set_inactive_state()
    
    def _reset_fields(self) -> None:
        self.target_name = None
        self.alert_distance = None
        self.targets = []
        self.alarm_name = None

        self.target_name_field.set_text("")
        self.alert_distance_field.set_text("")
        self.target_field.set_text("")
        self.alarm_field.set_text("")

        self.update_button_states()
        self.update_target_field()
