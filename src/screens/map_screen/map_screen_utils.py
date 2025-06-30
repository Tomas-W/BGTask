from typing import TYPE_CHECKING

import os
import glob

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from src.widgets.containers import CustomButtonRow
from src.widgets.buttons import CancelButton, ConfirmButton


from managers.device.device_manager import DM
from src.app_managers.permission_manager import PM

from src.utils.wrappers import log_time
from src.utils.logger import logger
from src.settings import STATE, SPACE


if TYPE_CHECKING:
    from managers.gps.gps_manager import GPSManager

class MapScreenUtils:

    CACHE_MAX_FILES = 300

    def __init__(self):
        pass
# ############ UI ############ #
    @log_time("MapScreenUtils._init_content")
    def _init_map_content(self):
        """Initialises the screens UI."""
        self.gps_manager: "GPSManager"
        # Replace scroll container with FloatLayout
        # Allows for full-screen map
        self.body = FloatLayout(size_hint=(1, 1))
        self.layout.remove_widget(self.scroll_container)
        self.layout.add_widget(self.body)

        # Build screen UI
        self._create_map_layout()
        self._create_bottom_buttons()        
        DM.INITIALIZED.MAP_SCREEN = True

    def _create_map_layout(self):
        """Adds the full-screen map."""
        from kivy_garden.mapview import MapView, MapSource

        source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_tiles=MapScreenUtils.CACHE_MAX_FILES,
            min_zoom=4,
            max_zoom=14,
            attribution="© OpenStreetMap contributors"
        )

        # Start with default coordinates
        self.mapview = MapView(
            zoom=17, 
            lat=self.gps_manager.DEFAULT_LAT, 
            lon=self.gps_manager.DEFAULT_LON,
            size_hint=(1, 1), pos=(0, 0),
            map_source=source,
            double_tap_zoom=True,
            pause_on_action=True,
            snap_to_zoom=True
        )
        self.mapview.bind(on_touch_down=self._on_map_touch_down,
                          on_touch_up=self._on_map_touch_up)

        self.body.add_widget(self.mapview)

        # Get location once and center map
        self.gps_manager.get_current_location(self.center_on_location)
    
    def center_on_location(self, lat, lon):
        """Centers the map on the given location."""
        logger.debug(f"Centering map on location: {lat}, {lon}")
        self.mapview.center_on(lat, lon)

    def _create_bottom_buttons(self):
        """Adds the cancel and select buttons."""
        btn_bar = BoxLayout(
            orientation="vertical",
            size_hint=(1, None), height=100,
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SCREEN_PADDING_X],
            pos_hint={"x": 0, "y": 0}
        )
        # Button row
        row = CustomButtonRow()
        btn_bar.add_widget(row)
        self.body.add_widget(btn_bar)
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=self._on_cancel)
        row.add_widget(self.cancel_button)
        # Select button
        self.select_button = ConfirmButton(text="Select", width=2,
                                           color_state=STATE.INACTIVE)
        self.select_button.bind(on_release=self._on_select)
        row.add_widget(self.select_button)
    
# ############ Markers ############ #
    def get_marker(self, lat: float, lon: float):
        """Returns a marker placed at the given lat/lon."""
        from kivy_garden.mapview import MapMarker
        return MapMarker(lat=lat, lon=lon)
    
    def _cancel_pending_marker(self):
        """Stops any scheduled marker event that hasn't executed yet."""
        if self._pending_marker_ev is not None:
            self._pending_marker_ev.cancel()
            self._pending_marker_ev = None
    
    def reset_marker_state(self):
        """Removes the current marker and resets the selected location."""
        self._cancel_pending_marker()
        self.remove_current_marker()
        self.reset_marker_location()

    def remove_current_marker(self):
        """Removes the current marker from the map."""
        if self.current_marker:
            self.mapview.remove_marker(self.current_marker)
            self.current_marker = None
    
    def save_marker_location(self, lat: float, lon: float):
        """Saves the selected location coordinates."""
        self.selected_lat = lat
        self.selected_lon = lon
    
    def reset_marker_location(self):
        """Resets the selected location coordinates."""
        self.selected_lat = None
        self.selected_lon = None
    
# ############ Misc ############ #
    def _request_location_permission(self):
        """Requests location permission if needed."""
        PM.validate_permission(PM.ACCESS_FINE_LOCATION)
        PM.validate_permission(PM.ACCESS_COARSE_LOCATION)
    
    @log_time("MapScreenUtils.clear_map_cache")
    def clear_map_cache(self):
        """Deletes all cached map tiles."""
        try:
            cache_dir = self._get_cache_dir()
            
            if os.path.exists(cache_dir):
                png_files = glob.glob(os.path.join(cache_dir, "**", "*.png"), recursive=True)
                for png_file in png_files:
                    try:
                        os.remove(png_file)
                    except OSError:
                        pass
                
                logger.info(f"Cleared {len(png_files)} cached map tiles on launch")
        
        except Exception as e:
            logger.warning(f"Failed to clear map cache: {e}")
    
    @log_time("MapScreenUtils.limit_map_cache")
    def limit_map_cache(self):
        """Limits the map cache to CACHE_MAX_FILES."""
        try:
            cache_dir = self._get_cache_dir()
            png_files = glob.glob(os.path.join(cache_dir, "**", "*.png"), recursive=True)
            
            if len(png_files) <= self.CACHE_MAX_FILES:
                return
            
            png_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_remove = len(png_files) - self.CACHE_MAX_FILES
            removed_count = 0
            for png_file in png_files[:files_to_remove]:
                try:
                    os.remove(png_file)
                    removed_count += 1
                except OSError:
                    pass
            
            logger.info(f"Limited map cache: removed {removed_count} old files, kept {len(png_files) - removed_count}")
        
        except Exception as e:
            logger.warning(f"Failed to limit map cache: {e}")
    
    def _get_cache_dir(self):
        """Returns the cache directory."""
        if DM.is_android:
            return os.path.join(os.environ.get("ANDROID_PRIVATE", ""), "cache")
        else:
            return os.path.join(os.getcwd(), "cache")
    
