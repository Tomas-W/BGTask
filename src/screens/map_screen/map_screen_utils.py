import os
import glob

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from src.widgets.containers import CustomButtonRow, CustomSettingsButtonRow
from src.widgets.buttons import CancelButton, ConfirmButton, SettingsConfirmButton


from managers.device.device_manager import DM
from src.app_managers.permission_manager import PM

from src.utils.wrappers import android_only, log_time
from src.utils.logger import logger
from src.settings import SIZE, STATE, SPACE


class MapScreenUtils:
    def __init__(self):
        pass
# ############ UI ############ #
    @log_time("MapScreenUtils._init_content")
    def _init_map_content(self):
        """Initialises the screens UI."""
        # Replace scroll container with FloatLayout
        # Allows for full-screen map
        self.body = FloatLayout(size_hint=(1, 1))
        self.layout.remove_widget(self.scroll_container)
        self.layout.add_widget(self.body)

        # Build screen UI
        self._create_map_layout()
        self._create_top_buttons()
        self._create_bottom_buttons()        
        DM.INITIALIZED.MAP_SCREEN = True

    def _create_map_layout(self):
        """Adds the full-screen map with error recovery."""
        try:
            self._create_mapview()
        except Exception as e:
            # Check if it's the SDL2 corruption error
            if "SDL2" in str(e):
                logger.warning("Map tile corruption detected, clearing cache and retrying...")
                self.clear_map_cache()
                # Retry map creation
                try:
                    self._create_mapview()
                except Exception as retry_error:
                    logger.error(f"Failed to create map even after cache clear: {retry_error}")
                    # Fallback placeholder
                    self._create_fallback_map()
            else:
                logger.error(f"Unexpected error creating map: {e}")
                raise

    def _create_mapview(self):
        """Creates the actual MapView widget."""
        from kivy_garden.mapview import MapView, MapSource

        source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_tiles=DM.SETTINGS.CACHE_MAX_FILES,
            min_zoom=4,
            max_zoom=14,
            attribution="© OpenStreetMap contributors"
        )

        self.mapview = MapView(
            zoom=17, 
            lat=DM.SETTINGS.DEFAULT_LAT, 
            lon=DM.SETTINGS.DEFAULT_LON,
            size_hint=(1, 1), pos=(0, 0),
            map_source=source,
            double_tap_zoom=False,
            pause_on_action=False,
            snap_to_zoom=True
        )
        self.mapview.bind(on_touch_down=self._on_map_touch_down,
                          on_touch_up=self._on_map_touch_up)

        self.body.add_widget(self.mapview)

    def _create_fallback_map(self):
        """Creates a basic fallback when map fails completely."""
        from kivy.uix.label import Label
        fallback_label = Label(
            text="Map temporarily unavailable\nRestart app to retry",
            text_size=(None, None),
            halign="center"
        )
        self.body.add_widget(fallback_label)
    
    def center_on_location(self, lat, lon):
        """Centers the map on the given location."""
        logger.debug(f"Centering map on location: {lat}, {lon}")
        self.mapview.center_on(lat, lon)

    def _create_top_buttons(self):
        """Adds the center marker and center location buttons at the top."""
        btn_bar = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.SETTINGS_BUTTON_HEIGHT,
            padding=[SPACE.SCREEN_PADDING_X, SPACE.SCREEN_PADDING_X],
            pos_hint={"x": 0, "top": 0.96}
        )
        # Button row
        row = CustomSettingsButtonRow()
        btn_bar.add_widget(row)
        self.body.add_widget(btn_bar)
        # Center on marker button
        self.center_marker_button = SettingsConfirmButton(
            text="Marker", 
            width=2,
        )
        self.center_marker_button.bind(on_release=self._on_center_marker)
        row.add_widget(self.center_marker_button)
        self.block_touch.append(self.center_marker_button)
        # Center on location button
        self.center_location_button = SettingsConfirmButton(
            text="Location", 
            width=2,
        )
        self.center_location_button.bind(on_release=self._on_center_location)
        row.add_widget(self.center_location_button)
        self.block_touch.append(self.center_location_button)
    
    def _create_bottom_buttons(self):
        """Adds the cancel and select buttons."""
        btn_bar = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.BUTTON_HEIGHT,
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
        self.block_touch.append(self.cancel_button)
        # Select button
        self.select_button = ConfirmButton(text="Select", width=2,
                                           color_state=STATE.INACTIVE)
        self.select_button.bind(on_release=self._on_select)
        row.add_widget(self.select_button)
        self.block_touch.append(self.select_button)
    
# ############ Markers ############ #
    def get_marker(self, lat: float, lon: float):
        """Returns a marker placed at the given lat/lon."""
        from kivy_garden.mapview import MapMarker
        return MapMarker(lat=lat, lon=lon)
    
    def reset_marker_state(self):
        """Removes the current marker and resets the selected location."""
        self.remove_current_marker()
        self.reset_marker_location()
        
        # Update button states
        self.select_button.set_inactive_state()
        self.center_marker_button.set_inactive_state()

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
    
# ############ GPS ############ #
    @android_only
    def _check_gps_availability(self) -> bool:
        """
        Check if GPS is available and can be used.
        Returns True if GPS is available, False otherwise.
        """
        try:
            # Import Android classes
            from jnius import autoclass  # type: ignore
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            LocationManager = autoclass('android.location.LocationManager')
            
            # Check if activity context is available
            if not hasattr(PythonActivity, 'mActivity') or PythonActivity.mActivity is None:
                logger.error("App GPS: Activity context not available")
                return False
            
            # Get location manager from activity context
            activity = PythonActivity.mActivity
            location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
            
            if location_manager is None:
                logger.error("App GPS: Could not get LocationManager")
                return False
            
            # Check if GPS provider is available
            gps_enabled = location_manager.isProviderEnabled(LocationManager.GPS_PROVIDER)
            if not gps_enabled:
                logger.warning("App GPS: GPS provider is disabled")
                return False
            
            # Check if GPS provider exists
            providers = location_manager.getAllProviders()
            if not providers or LocationManager.GPS_PROVIDER not in providers.toArray():
                logger.error("App GPS: GPS provider not available on device")
                return False
            
            logger.info("App GPS: GPS is available and enabled")
            # self._show_waiting_for_signal_popup()
            return True
            
        except ImportError as e:
            logger.error(f"App GPS: Android imports not available: {e}")
            return False
        except Exception as e:
            logger.error(f"App GPS: Error checking GPS availability: {e}")
            return False

    def _show_gps_unavailable_popup(self) -> None:
        """Show popup when GPS is not available."""
        from managers.popups.popup_manager import POPUP
        POPUP.show_confirmation_popup(
            header="Cannot track location",
            field_text="Enable GPS and reload screen.",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
    
    def _show_waiting_for_signal_popup(self) -> None:
        """Show popup when waiting for GPS signal."""
        from managers.popups.popup_manager import POPUP
        POPUP.show_confirmation_popup(
            header="Waiting for GPS signal",
            field_text="Connecting to satellite...",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
        self.center_location_button.set_inactive_state()
    
    def _show_center_on_location_popup(self) -> None:
        """Show popup when cannot center on location."""
        from managers.popups.popup_manager import POPUP
        POPUP.show_confirmation_popup(
            header="Cannot center on location",
            field_text="Enable GPS and reload screen.",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
            
    def _show_center_on_marker_popup(self) -> None:
        """Show popup when no marker is set."""
        from managers.popups.popup_manager import POPUP
        POPUP.show_confirmation_popup(
            header="Cannot center on marker",
            field_text="Place a marker and reload screen.",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )

# ############ Misc ############ #
    def _request_location_permission(self):
        """Requests location permission if needed."""
        PM.validate_permission(PM.ACCESS_FINE_LOCATION)
        PM.validate_permission(PM.ACCESS_BACKGROUND_LOCATION)
        
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
            
            if len(png_files) <= DM.SETTINGS.CACHE_MAX_FILES:
                return
            
            png_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_remove = len(png_files) - DM.SETTINGS.CACHE_MAX_FILES
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
    
