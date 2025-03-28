from kivy.app import App

from src.utils.containers import TopBarContainer
from src.utils.buttons import TopBarTitle, TopBarButton

from src.settings import SPACE, SIZE, COL, STYLE, FONT, PATH, SCREEN


class HomeBarClosed():
    """
    HomeBar is the TopBar of the HomeScren that:
    - Has an Edit button for editing/removing tasks
    - Has an new_task button for creating new tasks
    - Has an options_button for showing/hiding options
    """
    def __init__(self,
                 edit_callback,
                 new_task_callback,
                 options_callback,
                 ):
        self.top_bar_container = TopBarContainer()

        self.edit_button = TopBarButton(img_path=PATH.EDIT_IMG, radius_side="right")
        self.edit_button.bind(on_press=edit_callback)

        self.new_task_button = TopBarTitle(text="+")
        self.new_task_button.bind(on_press=new_task_callback)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.edit_button)
        self.top_bar_container.add_widget(self.new_task_button)
        self.top_bar_container.add_widget(self.options_button)


class HomeBarExpanded():
    """
    HomeBarExpanded is the TopBar of the HomeScren that:
    - Has an Edit button for editing/removing tasks
    - Has NO new_task button for creating new tasks
    - Has a settings_button for opening the SettingsScreen
    - Has an exit_button for exiting the app
    - Has an options_button for showing/hiding options
    """
    def __init__(self,
                 edit_callback,
                 screenshot_callback,
                 options_callback,
                 settings_callback,
                 exit_callback,
                 ):
        self.top_bar_container = TopBarContainer()

        self.edit_button = TopBarButton(img_path=PATH.EDIT_IMG, radius_side="right")
        self.edit_button.bind(on_press=edit_callback)

        self.new_task_button = TopBarTitle(button=False)

        self.screenshot_button = TopBarButton(img_path=PATH.SCREENSHOT_IMG, radius_side="left")
        self.screenshot_button.bind(on_press=screenshot_callback)

        self.settings_button = TopBarButton(img_path=PATH.SETTINGS_IMG, radius_side="none")
        self.settings_button.bind(on_press=settings_callback)

        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, radius_side="none")
        self.exit_button.bind(on_press=exit_callback)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG_BLACK, radius_side="none")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.edit_button)
        self.top_bar_container.add_widget(self.new_task_button)
        self.top_bar_container.add_widget(self.screenshot_button)
        self.top_bar_container.add_widget(self.settings_button)
        self.top_bar_container.add_widget(self.exit_button)
        self.top_bar_container.add_widget(self.options_button)


class TopBarClosed():
    """
    TopBarClosed is the TopBar of the non HomeScreens that:
    - Has a title
    - Has an back_button for going back
    - Has an options_button for showing/hiding options [settings & exit]
    """
    def __init__(self,
                 bar_title,
                 back_callback,
                 options_callback,
                 **kwargs):
        super().__init__(**kwargs)
        self.top_bar_container = TopBarContainer()

        self.back_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.back_button.bind(on_press=back_callback)

        self.bar_title = TopBarTitle(text=bar_title, button=False)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG, radius_side="left")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.back_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.options_button)


class TopBarExpanded():
    """
    TopBarExpanded is the TopBar of the non HomeScreens that:
    - Has NO title
    - Has an back_button for going back
    - Has a settings_button for opening the SettingsScreen
    - Has an exit_button for exiting the app
    - Has an options_button for showing/hiding options
    """
    def __init__(self,
                 back_callback,
                 screenshot_callback,
                 options_callback,
                 settings_callback,
                 exit_callback,
                 **kwargs):
        super().__init__(**kwargs)
        self.top_bar_container = TopBarContainer()

        self.back_button = TopBarButton(img_path=PATH.BACK_IMG, radius_side="right")
        self.back_button.bind(on_press=back_callback)

        self.bar_title = TopBarTitle(button=False)

        self.screenshot_button = TopBarButton(img_path=PATH.SCREENSHOT_IMG, radius_side="left")
        self.screenshot_button.bind(on_press=screenshot_callback)

        self.settings_button = TopBarButton(img_path=PATH.SETTINGS_IMG, radius_side="none")
        self.settings_button.bind(on_press=settings_callback)

        self.exit_button = TopBarButton(img_path=PATH.EXIT_IMG, radius_side="none")
        self.exit_button.bind(on_press=exit_callback)

        self.options_button = TopBarButton(img_path=PATH.OPTIONS_IMG_BLACK, radius_side="none")
        self.options_button.bind(on_press=options_callback)

        self.top_bar_container.add_widget(self.back_button)
        self.top_bar_container.add_widget(self.bar_title)
        self.top_bar_container.add_widget(self.screenshot_button)
        self.top_bar_container.add_widget(self.settings_button)
        self.top_bar_container.add_widget(self.exit_button)
        self.top_bar_container.add_widget(self.options_button)
