from kivy.uix.label import Label
from src.settings import COL, SIZE, SPACE, FONT


class PartitionHeader(Label):
    """
    PartitionHeader is a header for a partition that:
    - Can be aligned (center by default)
    """
    def __init__(self, text: str, halign: str = "center", valign: str = "center", **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            height=SIZE.BUTTON_HEIGHT,
            halign=halign,
            valign=valign,
            font_size=FONT.HEADER,
            bold=True,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))


class ButtonFieldLabel(Label):
    """
    ButtonFieldLabel is a label for a CustomButton
    """
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            **kwargs
        )

        self.bind(size=self.setter("text_size"))
