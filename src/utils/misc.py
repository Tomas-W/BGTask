from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from src.settings import SPACE, COL


class Spacer(BoxLayout):
    def __init__(self, height=SPACE.SPACE_M, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(height),
            **kwargs
        )
        with self.canvas.before:
            Color(*COL.FIELD_ERROR)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self.update_rect, pos=self.update_rect)

    def update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
