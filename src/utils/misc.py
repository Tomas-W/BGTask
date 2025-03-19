from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from src.settings import SPACE


class Spacer(BoxLayout):
    def __init__(self, height=SPACE.SPACE_Y_XL, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(height),
            **kwargs
        )
