from typing import Any, Callable

from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from src.settings import COL, SPACE


class BasePopup(Popup):
    """Base class for all popups"""
    def __init__(self, **kwargs):
        # Holds the Widgets
        self.content_layout = BoxLayout(
            orientation="vertical",
            padding=[SPACE.SPACE_S, SPACE.SPACE_S, SPACE.SPACE_S, SPACE.SPACE_L],
        )
        
        super().__init__(
            title="",
            content=self.content_layout,
            size_hint=(1, None),
            height=1,
            background="",
            background_color=COL.BG_POPUP,
            separator_height=0,
            auto_dismiss=False,
            **kwargs
        )
        self.content_layout.bind(minimum_height=self._update_height)

        # Store callbacks
        self._confirm_handler: Callable | None = None
        self._cancel_handler: Callable | None = None
        # TaskPopup has its own handlers (snooze_a, snooze_b, cancel)

    def _update_height(self, instance, value: float) -> None:
        """Update popup height based on content"""
        self.height = value + SPACE.SPACE_XL
    
    def _update_text_size(self, instance, value: float) -> None:
        """Update text_size to enable text wrapping based on width"""
        width = self.width - SPACE.SPACE_XL
        self.header.text_size = (width, None)
        
    def _update_label_height(self, instance, value: float) -> None:
        """Update label height to match its texture height"""
        texture_height = instance.texture_size[1]
        instance.height = texture_height
    
    def _safe_call(self, func: Callable, arg: Any | None = None) -> Any:
        """Call a function that might expect arguments"""
        import inspect
        if func:
            sig = inspect.signature(func)
            if len(sig.parameters) == 0:
                return func()
            else:
                return func(arg)
    
    def show_animation(self, *args) -> None:
        """Show popup with fade animation"""
        self.opacity = 0
        self.open()
        
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)
    
    def hide_animation(self, on_complete: Callable | None = None) -> None:
        """Hide popup immediately and call callback"""
        self.dismiss()
        if on_complete:
            on_complete()