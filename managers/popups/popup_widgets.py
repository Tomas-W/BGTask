from typing import TYPE_CHECKING

from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label

from src.settings import COL, FONT, SPACE, STYLE, SIZE

if TYPE_CHECKING:
    from managers.tasks.task import Task


class TaskPopupContainer(BoxLayout):
    """
    A TaskPopupContainer is used to display an expired Task in a popup.
    """
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            padding=[SPACE.TASK_PADDING_X, SPACE.TASK_PADDING_Y],
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))
        
        with self.canvas.before:
            self.bg_color = Color(*COL.FIELD_INPUT)
            self.bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
                radius=[STYLE.RADIUS_M]
            )
            self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class TaskPopupHeader(Label):
    """
    A TaskPopupHeader displays: "Task Expired!"
    """
    def __init__(self, text: str,**kwargs):
        super().__init__(
            text=text,
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            halign="center",
            font_size=FONT.HEADER,
            bold=True,
            color=COL.TEXT_GREY,
            **kwargs
        )
        self.bind(size=self.setter("text_size"))
    
    def set_text(self, text: str):
        self.text = text


class TaskPopupLabel(Label):
    """
    A TaskPopupLabel is a label for displaying task info in popups.
    Similar to TaskInfoLabel but without touch functionality or selection states.
    """
    def __init__(self, **kwargs):
        super().__init__(
            text="",
            size_hint=(1, None),
            halign="left",
            valign="top",
            font_size=FONT.DEFAULT,
            color=COL.TEXT,
            markup=True,
            **kwargs
        )
        self.bind(width=self._update_text_size)
        self.bind(texture_size=self._update_height)

    def set_task_details(self, task: "Task"):
        """Sets the task information and updates the display text."""
        # Format the task info text
        time = task.get_time_str()
        snooze_time = f"+ {task.get_snooze_str()}" if task.snooze_time else ""
        message = task.message
        
        # Convert RGBA tuples to hex color strings
        text_color = "#{:02x}{:02x}{:02x}".format(
            int(COL.TEXT[0] * 255), int(COL.TEXT[1] * 255), int(COL.TEXT[2] * 255))
        snooze_color = "#{:02x}{:02x}{:02x}".format(
            int(COL.SNOOZE[0] * 255), int(COL.SNOOZE[1] * 255), int(COL.SNOOZE[2] * 255))

        task_info_text = f"[size={FONT.DEFAULT}][color={text_color}][b]{time}[/b][/color][/size]  [size={FONT.SMALL}][color={snooze_color}]{snooze_time}[/color][/size][size={FONT.DEFAULT}]\n[color={text_color}]{message}[/color][/size]"
        
        self.text = task_info_text

    def _update_text_size(self, instance, value):
        """Updates text_size when width changes to enable proper text wrapping."""
        if self.width > 0:
            # Use full width - Label handles padding internally
            self.text_size = (self.width, None)

    def _update_height(self, instance, value):
        """Updates the widget height based on the texture size."""
        if self.texture_size[1] > 0:
            # Use texture height directly - Label handles padding internally
            self.height = self.texture_size[1]