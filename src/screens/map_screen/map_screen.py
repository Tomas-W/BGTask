from kivy.clock import Clock
from kivy.uix.widget import Widget
from typing import TYPE_CHECKING

from src.screens.base.base_screen import BaseScreen
from .map_screen_utils import MapScreenUtils

from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_communication_manager import AppCommunicationManager
    from kivy.uix.widget import Widget
    from kivy_garden.mapview import Marker
    from kivy.clock import ClockEvent


class MapScreen(BaseScreen, MapScreenUtils):

    SCROLL_MOVEMENT_THRESHOLD: int = 10  # pixels
    DOUBLE_TAP_DELAY: float = 0.30       # seconds
    CACHE_MAX_FILES: int = 350           # nr files

    """
    MapScreen displays a world map and:
    - Has a top bar with a back button, options button, and exit button
    - Allows navigating the world map
    - Allows selecting a location and save its coordinates
    """
    
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.communication_manager: "AppCommunicationManager" = app.communication_manager

        # Selection
        self.current_marker: "Marker | None" = None
        self.selected_lat: float | None = None
        self.selected_lon: float | None = None
        # Double tap prevention
        self.last_tap_time: float = 0
        self._pending_marker_ev: "ClockEvent | None" = None
        
        # Location state
        self.has_user_location: bool = False
        self.user_lat: float | None = None
        self.user_lon: float | None = None

        # Block touch on
        self.block_touch: list["Widget"] = []
        
        # TopBar title
        self.top_bar.bar_title.set_text("Select Location")
        
        # Add location permission check
        self._request_location_permission()
    
    def _on_map_touch_down(self, instance, touch) -> bool:
        """Saves the start position of the touch."""
        if self.mapview.collide_point(*touch.pos):
            touch.ud["start_pos"] = touch.pos
        return False

    def _on_map_touch_up(self, instance, touch) -> bool:
        """
        Checks if the touch is a:
        - Touch outside map -> ignore
        - Mouse wheel events -> zoom
        - Double tap -> cancel pending marker and zoom
        - Drag / scroll -> scroll
        - Single tap -> schedule marker
        """
        # Touch outside map -> ignore
        if not self.mapview.collide_point(*touch.pos):
            return False
        
        # Touch on blocked widgets -> ignore
        for widget in self.block_touch:
            if widget.collide_point(*touch.pos):
                return False
        
        # Mouse wheel events -> zoom
        if hasattr(touch, "button") and touch.button in ["scrollup", "scrolldown"]:
            return False
        
        # Double tap -> cancel pending marker and zoom
        if touch.is_double_tap:
            self._cancel_pending_marker()
            return False
        
        # Drag / scroll -> scroll
        start = touch.ud.get("start_pos", touch.pos)
        movement = abs(start[0] - touch.pos[0]) + abs(start[1] - touch.pos[1])
        if movement >= MapScreen.SCROLL_MOVEMENT_THRESHOLD:
            return False
        
        # Single tap -> schedule marker
        self._cancel_pending_marker()
        self._pending_marker_ev = Clock.schedule_once(
            lambda dt, p=touch.pos: self._place_marker(p),
            MapScreen.DOUBLE_TAP_DELAY,
        )
        return True
    
    def _place_marker(self, pos: tuple[float, float]) -> None:
        """Removes any previous marker and places a new one at the position."""
        # Reset
        self._pending_marker_ev = None
        self.reset_marker_state()
        # Place marker
        lat, lon = self.mapview.get_latlon_at(*pos)
        self.current_marker = self.get_marker(lat, lon)
        self.mapview.add_marker(self.current_marker)
        # Update coordinates
        self.selected_lat, self.selected_lon = lat, lon
        # Update button states
        self.select_button.set_active_state()
        self.center_marker_button.set_active_state()
    
    def _on_center_marker(self, instance) -> None:
        """Centers the map on the current marker."""
        self.center_on_marker()
    
    def _on_center_location(self, instance) -> None:
        """Centers the map on the user's location."""
        self.center_on_user_location()
    
    def _on_cancel(self, instance) -> None:
        """Resets marker and coordinates and navigates back to HomeScreen."""
        self.reset_marker_state()
        self.navigation_manager.navigate_back_to(DM.SCREEN.HOME)
    
    def _on_select(self, instance) -> None:
        """Saves the selected coordinates and starts monitoring."""
        if self.selected_lat is None or self.selected_lon is None:
            logger.warning("No location selected")
            return
        
        self.save_marker_location(self.selected_lat, self.selected_lon)
        
        # Send GPS monitoring request to service with selected coordinates
        logger.info(f"Starting GPS monitoring for coordinates: {self.selected_lat}, {self.selected_lon}")
        self.communication_manager.send_gps_monitoring_action(self.selected_lat, self.selected_lon)
        
        self.reset_marker_state()
        self.navigation_manager.navigate_back_to(DM.SCREEN.HOME)
    
    def _request_current_location(self) -> None:
        """Requests current location from service."""
        logger.info("Requesting current location from service...")
        self.communication_manager.send_action(DM.ACTION.GET_LOCATION_ONCE)
    
    def handle_location_response(self, lat: float | None, lon: float | None) -> None:
        """Handles location response from service."""
        if lat is not None and lon is not None:
            logger.info(f"Map screen received location: {lat}, {lon}")
            self.user_lat = lat
            self.user_lon = lon
            self.has_user_location = True
            
            # Update center location button state
            self.center_location_button.set_active_state()
        
        else:
            logger.warning("Map screen: No location available")
            self.has_user_location = False
            self.center_location_button.set_inactive_state()
    
    def center_on_marker(self) -> None:
        """Centers the map on the current marker."""
        if self.current_marker:
            logger.info(f"Centering map on marker: {self.selected_lat}, {self.selected_lon}")
            self.mapview.center_on(self.selected_lat, self.selected_lon)
    
    def center_on_user_location(self) -> None:
        """Centers the map on the user's location."""
        if self.has_user_location and self.user_lat and self.user_lon:
            logger.info(f"Centering map on user location: {self.user_lat}, {self.user_lon}")
            self.mapview.center_on(self.user_lat, self.user_lon)
    
    def on_pre_enter(self) -> None:
        """Called before the screen is entered."""
        self._request_current_location()
        
        super().on_pre_enter()
        
        if self.current_marker:
            self.select_button.set_active_state()
            self.center_marker_button.set_active_state()
        else:
            self.select_button.set_inactive_state()
            self.center_marker_button.set_inactive_state()
        
        if self.has_user_location:
            self.center_location_button.set_active_state()
        else:
            self.center_location_button.set_inactive_state()
        
        self.limit_map_cache()

    def _on_map_view_change(self, instance, value) -> None:
        """Handles map view changes (zoom, pan, etc)."""
        # Force map to update tiles
        if hasattr(self.mapview, "_trigger_update"):
            self.mapview._trigger_update(0)  # Immediate update
