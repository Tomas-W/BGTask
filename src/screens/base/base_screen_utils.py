from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle


from kivy.uix.label import Label
from kivy.clock import Clock
from src.settings import COL, FONT, SIZE


class FPSCounter(Label):

    UPDATE_INTERVAL: float = 0.5
    """
    FPS counter using Kivy's built-in FPS tracking.
    """
    def __init__(self, **kwargs):
        super().__init__(
            text="FPS: 0",
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            halign="right",
            valign="middle",
            font_size=FONT.DEFAULT,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))

        with self.canvas.before:
            self.bg_color = Color(*COL.BG)
            self.bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )
            self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Update FPS display every UPDATE_INTERVAL
        Clock.schedule_interval(self.update_fps, FPSCounter.UPDATE_INTERVAL)
    
    def _update_bg(self, instance, value: float) -> None:
        """Updates the background size of the FPSCounter."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def update_fps(self, dt):
        """Updates the FPS display using Kivy's built-in FPS."""
        fps = Clock.get_fps()
        self.text = f"FPS: {fps:.1f}"
