from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout

from src.settings import SPACE, COL


class Spacer(BoxLayout):
    """
    Spacer is a box layout that:
    - Has a height
    - Has a background color (default is transparent)
    """
    def __init__(self, height=SPACE.SPACE_M, color=COL.OPAQUE, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=height,
            **kwargs
        )
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update, pos=self._update)

    def _update(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
