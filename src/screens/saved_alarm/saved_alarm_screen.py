from kivy.uix.floatlayout import FloatLayout

from src.screens.base.base_screen import BaseScreen

from src.utils.bars import TopBarClosed, TopBarExpanded
from src.utils.containers import Partition, ScrollContainer, BaseLayout, CustomButtonRow
from src.utils.buttons import CustomButton, CustomSettingsButton

from src.settings import STATE, SCREEN

class SavedAlarmScreen(BaseScreen):
    """
    SavedAlarmScreen is the screen for selecting a saved alarm.
    """
    def __init__(self, navigation_manager, task_manager, audio_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.audio_manager = audio_manager

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = TopBarClosed(
            bar_title="Saved Alarms",
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM),
            options_callback=lambda instance: self.switch_top_bar(),
        )
        # Top bar with expanded options
        self.top_bar_expanded = TopBarExpanded(
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM),
            screenshot_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.START),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=lambda instance: self.navigation_manager.exit_app(),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Alarm picker partition
        self.alarm_picker_partition = Partition()
        # Alarm picker buttons
        self.create_alarm_buttons()
        # Add to scroll container
        self.scroll_container.container.add_widget(self.alarm_picker_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.confirmation_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomButton(
            text="Cancel",
            color_state=STATE.INACTIVE,
        )
        self.cancel_button.bind(on_press=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM))
        self.confirmation_row.add_widget(self.cancel_button)
        # Confirm button
        self.confirm_button = CustomButton(
            text="Select",
            color_state=STATE.INACTIVE,
        )
        self.confirm_button.bind(on_press=self.confirm_alarm_selection)
        self.confirmation_row.add_widget(self.confirm_button)
        # Add to confirmation partition
        self.confirmation_partition.add_widget(self.confirmation_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

    def confirm_alarm_selection(self, instance):
        """
        Confirm the alarm selection.
        """

        self.navigation_manager.navigate_back_to(SCREEN.SELECT_ALARM)

    def create_alarm_buttons(self):
        """
        Create the alarm buttons for the alarm picker partition.
        """
        for name, path in self.audio_manager.alarms.items():
            button = CustomSettingsButton(
                text=name,
                width=1,
                color_state=STATE.INACTIVE,
            )
            button.bind(on_press=self.select_alarm)
            self.alarm_picker_partition.add_widget(button)

    def select_alarm(self, instance):
        """
        Select the alarm.
        """
        self.audio_manager.set_alarm_name(name=instance.text)
        self.audio_manager.set_alarm_path(name=instance.text)
        for button in self.alarm_picker_partition.children:
            if button.text == self.audio_manager.selected_alarm_name:
                button.set_active_state()
            else:
                button.set_inactive_state()
        self.confirm_button.set_active_state()
    
    def on_pre_enter(self):
        """
        Called when the screen is entered.
        """
        super().on_pre_enter()
        self.alarm_picker_partition.clear_widgets()
        self.create_alarm_buttons()
