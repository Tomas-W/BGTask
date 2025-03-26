from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from src.settings import COL, FONT, SIZE, SPACE


from src.utils.containers import TopBarContainer
from src.utils.buttons import TopBarTitle, TopBarButton

from src.settings import PATH


class SelectAlarmBar():
    """
    SelectAlarmBar is the TopBar of the SelectAlarmScreen that:
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

        self.new_task_button = TopBarTitle(text="Select Date", button=False)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.back_button)
        self.top_bar_container.add_widget(self.new_task_button)
        self.top_bar_container.add_widget(self.options_button)


class SelectDateBarExpanded():
    """
    SelectAlarmBarExpanded is the TopBar of the SelectAlarmScreen that:
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

        self.new_task_button = TopBarTitle(button=False)

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