from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from src.settings import COL, FONT, SIZE, SPACE


from src.utils.containers import TopBarContainer
from src.utils.buttons import TopBar, TopBarButton

from src.settings import PATH


class SelectDateBar():
    """
    SelectDateBar is the TopBar of the SelectDateScreen that:
    - Has an Edit button for editing/removing tasks
    - Has an new_task button for creating new tasks
    - Has an options_button for showing/hiding options
    """
    def __init__(self,
                 back_callback,
                 options_callback,
                 **kwargs):
        super().__init__(**kwargs)
        self.top_bar_container = TopBarContainer()

        self.back_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.back_button.bind(on_press=back_callback)

        self.new_task_button = TopBar(text="Select Date", button=False)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.back_button)
        self.top_bar_container.add_widget(self.new_task_button)
        self.top_bar_container.add_widget(self.options_button)


class SelectDateBarExpanded():
    """
    SelectDateBarExpanded is the TopBar of the SelectDateScreen that:
    - Has an Edit button for editing/removing tasks
    - Has an new_task button for creating new tasks
    - Has a settings_button for opening the SettingsScreen
    - Has an exit_button for exiting the app
    - Has an options_button for showing/hiding options
    """
    def __init__(self,
                 back_callback,
                 options_callback,
                 settings_callback,
                 exit_callback,
                 **kwargs):
        super().__init__(**kwargs)
        self.top_bar_container = TopBarContainer()

        self.back_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.back_button.bind(on_press=back_callback)

        self.new_task_button = TopBar(button=False)

        self.settings_button = TopBarButton(img_path=PATH.SETTINGS_IMG, radius_side="left")
        self.settings_button.bind(on_press=settings_callback)

        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, radius_side="none")
        self.exit_button.bind(on_press=exit_callback)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG_BLACK, radius_side="none")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.back_button)
        self.top_bar_container.add_widget(self.new_task_button)
        self.top_bar_container.add_widget(self.settings_button)
        self.top_bar_container.add_widget(self.exit_button)
        self.top_bar_container.add_widget(self.options_button)
        

class CalendarContainer(BoxLayout):
    """Container for the calendar"""
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=SIZE.CALENDAR_HEIGHT,
            spacing=SPACE.SPACE_S,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class CalendarHeadersContainer(GridLayout):
    """GridLayout for the calendar headers"""
    def __init__(self, **kwargs):
        super().__init__(
            cols=7,
            size_hint=(1, None),
            height=SIZE.HEADER_HEIGHT,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))


class CalendarHeaderLabel(Label):
    """Label for the calendar header"""
    def __init__(self, text, **kwargs):
        super().__init__(
            text=text,
            bold=True,
            color=COL.TEXT,
            font_size=FONT.DEFAULT,
            size_hint_y=None,
            height=FONT.DEFAULT,
            **kwargs
        )
        self.bind(height=self.setter("height"))


class CalendarGrid(GridLayout):
    """GridLayout for the calendar"""
    def __init__(self, **kwargs):
        super().__init__(
            cols=7,
            size_hint=(1, None),
            height=7 * SIZE.HEADER_HEIGHT,  # Max 6 weeks, add 1 for spacing below
            **kwargs
        )
        self.bind(height=self.setter("height"))


class DateTimeLabel(ButtonBehavior, Label):
    """Label that behaves like a button"""
    def __init__(self, **kwargs):
        super().__init__(
            font_size=FONT.DEFAULT,
            color=COL.TEXT_GREY,
            bold=True,
            size_hint_y=None,
            height=SIZE.DATE_TIME_LABEL,
            halign="center",
            **kwargs
        )
        self.bind(size=self.setter("text_size"))

    def set_bold(self, is_bold):
        """Set the font size to make the text bold or normal"""
        if is_bold:
            self.font_size = FONT.DEFAULT_BOLD
        else:
            self.font_size = FONT.DEFAULT
