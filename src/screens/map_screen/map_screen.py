import glob
import os
from kivy.clock import Clock
from plyer import gps
from typing import TYPE_CHECKING

from src.screens.base.base_screen import BaseScreen
from src.utils.wrappers import log_time
from .map_screen_utils import MapScreenUtils

from managers.device.device_manager import DM

from src.utils.logger import logger

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager


class MapScreen(BaseScreen, MapScreenUtils):

    SCROLL_MOVEMENT_THRESHOLD = 10  # pixels
    DOUBLE_TAP_DELAY = 0.30         # seconds
    CACHE_MAX_FILES = 350
    """
    MapScreen displays a world map and:
    - Has a top bar with a back button, options button, and exit button
    - Allows navigating the world map
    - Allows selecting one location and save its coordinates
    """
    
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        
        # Selection
        self.current_marker = None
        self.selected_lat = None
        self.selected_lon = None
        # Double tap prevention
        self.last_tap_time = 0
        self._pending_marker_ev = None  # ClockEvent
        
        # TopBar title
        self.top_bar.bar_title.set_text("Select Location")
        
        # Add location permission check
        self._request_location_permission()
    
    def _on_map_touch_down(self, instance, touch):
        """Saves the start position of the touch."""
        if self.mapview.collide_point(*touch.pos):
            touch.ud["start_pos"] = touch.pos
        return False

    def _on_map_touch_up(self, instance, touch):
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
    
    def _place_marker(self, pos):
        """Removes any previous marker and places a new one at the touch position."""
        # Reset
        self._pending_marker_ev = None
        self.reset_marker_state()
        # Place marker
        lat, lon = self.mapview.get_latlon_at(*pos)
        self.current_marker = self.get_marker(lat, lon)
        self.mapview.add_marker(self.current_marker)
        # Update coordinates
        self.selected_lat, self.selected_lon = lat, lon
        # Update button state
        self.select_button.set_active_state()
    
    def _on_cancel(self, instance):
        """Resets marker and coordinates and navigates back to HomeScreen."""
        self.reset_marker_state()
        self.navigation_manager.navigate_back_to(DM.SCREEN.HOME)
    
    def _on_select(self, instance):
        """Saves the selected coordinates, resets marker and navigates back to HomeScreen."""
        if self.selected_lat is None or self.selected_lon is None:
            logger.warning("No location selected")
            return
        
        self.save_location(self.selected_lat, self.selected_lon)
        self.reset_marker_state()
        self.navigation_manager.navigate_back_to(DM.SCREEN.HOME)
    
    def on_pre_enter(self):
        """Called before the screen is entered."""
        super().on_pre_enter()
        
        if self.current_marker:
            self.select_button.set_active_state()
        else:
            self.select_button.set_inactive_state()
        
        self.limit_map_cache()

    def _on_map_view_change(self, instance, value):
        """Handles map view changes (zoom, pan, etc)."""
        # Force map to update tiles
        if hasattr(self.mapview, "_trigger_update"):
            self.mapview._trigger_update(0)  # Immediate update
