import calendar
from typing import TYPE_CHECKING

from datetime import datetime, date

from src.screens.base.base_screen import BaseScreen
from .select_date_utils import SelectDateUtils
from .select_date_widgets import TimeInputField

from src.widgets.buttons import ConfirmButton, CancelButton, SettingsButton
from src.widgets.containers import CustomButtonRow, Partition, CustomRow, CustomSettingsButtonRow
from src.widgets.labels import PartitionHeader

from managers.popups.popup_manager import POPUP

from managers.device.device_manager import DM
from src.utils.logger import logger
from src.settings import SPACE, STATE, COL

if TYPE_CHECKING:
    from main import TaskApp
    from src.app_managers.navigation_manager import NavigationManager
    from src.app_managers.app_task_manager import TaskManager


class SelectDateScreen(BaseScreen, SelectDateUtils):
    def __init__(self, app: "TaskApp", **kwargs):
        super().__init__(**kwargs)
        self.app: "TaskApp" = app
        self.navigation_manager: "NavigationManager" = app.navigation_manager
        self.task_manager: "TaskManager" = app.task_manager

        # Initialize current month/year for calendar view
        self.current_month: int = datetime.now().month
        self.current_year: int = datetime.now().year
        
        # TopBar title
        self.top_bar.bar_title.set_text("Select Date")

        self.scroll_container.container.spacing = SPACE.SPACE_XL

        # Select month partition
        self.select_month_partition = Partition()
        # Select month row
        self.select_month_row = CustomSettingsButtonRow()
        # Previous month button
        self.prev_month_button = SettingsButton(
            text="<",
            width=0.6,
            symbol=True,
            color_state=STATE.ACTIVE,
            color=COL.TEXT,
            bg_color=COL.TASK_SELECTED,
        )
        self.prev_month_button.bind(on_press=self.go_to_prev_month)
        # Select month label
        month_name = calendar.month_name[self.current_month]
        self.month_label = PartitionHeader(text=f"{month_name} {self.current_year}")
        # Next month button
        self.next_month_button = SettingsButton(
            text=">",
            width=0.6,
            symbol=True,
            color_state=STATE.ACTIVE,
            color=COL.TEXT,
            bg_color=COL.TASK_SELECTED,
        )
        self.next_month_button.bind(on_press=self.go_to_next_month)
        # Apply month row
        self.select_month_row.add_widget(self.prev_month_button)
        self.select_month_row.add_widget(self.month_label)
        self.select_month_row.add_widget(self.next_month_button)
        self.select_month_partition.add_widget(self.select_month_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.select_month_partition)

        # Select time partition
        self.select_time_partition = Partition()
        self.select_time_partition.spacing = SPACE.SPACE_L
        # Date label
        self.selected_date_label = PartitionHeader(text="")
        self.select_time_partition.add_widget(self.selected_date_label)
        # Time selection row
        self.select_time_row = CustomRow()
        # Time input
        self.time_input = TimeInputField()
        self.select_time_row.add_widget(self.time_input)
        self.select_time_partition.add_widget(self.select_time_row)
        # Add to scroll container
        self.scroll_container.container.add_widget(self.select_time_partition)

        # Calendar partition
        self.select_day_partition = Partition()
        self.create_calendar_grid()
        self.scroll_container.container.add_widget(self.select_day_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        self.confirmation_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=lambda instance: self.navigation_manager.navigate_back_to(DM.SCREEN.NEW_TASK))
        # Confirm button
        self.confirm_button = ConfirmButton(text="Confirm", width=2,
                                                  color_state=STATE.ACTIVE)
        self.confirm_button.bind(on_release=self.confirm_date_selection)
        # Apply confirmation partition
        self.confirmation_row.add_widget(self.cancel_button)
        self.confirmation_row.add_widget(self.confirm_button)
        self.confirmation_partition.add_widget(self.confirmation_row)
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add callback property
        self.callback = None
    
    def select_day(self, day: int) -> None:
        """
        Select a day from the calendar.
        Called when a day button is pressed.
        """
        try:
            selected_date = date(self.current_year, self.current_month, day)
            self.task_manager.selected_date = selected_date
            
            # If time not set yet, initialize it
            if not self.task_manager.selected_time:
                now = datetime.now().time()
                self.task_manager.selected_time = now
                self.time_input.set_text(now)
                
            # Highlight selected day
            self.update_calendar()
            
            # Update date label
            date_str = selected_date.strftime(DM.DATE.CALENDAR_DAY)
            self.selected_date_label.set_text(f"{date_str}")

        except ValueError:
            pass
    
    def validate_time(self) -> bool:
        """Validate the time input"""
        time_tuple = self.time_input.get_time()
        if time_tuple is None:
            self.time_input.show_error_border()
            return False
        
        self.time_input.hide_border()
        return True
    
    def update_task_manager_time(self) -> bool:
        """Update the task manager's selected time after user selection"""
        # Ensure we have a selected date
        if not self.task_manager.selected_date:
            self.task_manager.selected_date = datetime.now().date()
            
        # Update selected time in task_manager
        try:
            time_tuple = self.time_input.get_time()
            
            hours, minutes = time_tuple
            current_time = self.task_manager.selected_time or datetime.now().time()
            updated_time = current_time.replace(hour=hours, minute=minutes)
            self.task_manager.selected_time = updated_time
            return True

        except ValueError:
            return False
    
    def check_date_is_taken(self) -> bool:
        """
        Check if the date is taken by an existing task.
        If so, show a popup to the user to ask if they want to edit the existing task or
         select a different date.
        """
        date = datetime.combine(self.task_manager.selected_date, self.task_manager.selected_time)
        if self.task_manager.date_is_taken(date):
            self.show_date_is_taken_popup()
            return True
        
        return False
    
    def show_date_is_taken_popup(self) -> None:
        """Show a popup to the user to ask if they want to edit the existing task"""
        POPUP.show_custom_popup(
                header="Existing task found for:",
                field_text=f"{self.task_manager.selected_date} at {self.task_manager.selected_time.strftime(DM.DATE.SELECTED_TIME)}",
                extra_info="Cancel to resume selection\nEdit to update existing task",
                confirm_text="Edit",
                on_confirm=self.edit_existing_task,
                on_cancel=lambda: None
            )
    
    def confirm_date_selection(self, instance) -> None:
        """Return to new task screen, passing selected date"""
        if not self.validate_time():
            return
        
        if not self.update_task_manager_time():
            return

        if self.check_date_is_taken():
            return
        
        if self.task_is_in_past():
            self.show_date_in_past_popup()
            return
        
        # Handle callback
        if self.callback:
            self.callback(self.task_manager.selected_date, self.task_manager.selected_time)

        self.navigation_manager.navigate_back_to(DM.SCREEN.NEW_TASK)
    
    def task_is_in_past(self) -> bool:
        """Check if the task is in the past"""
        date = datetime.combine(self.task_manager.selected_date, self.task_manager.selected_time)
        return date < datetime.now()
    
    def show_date_in_past_popup(self) -> None:
        """Show a popup to the user to ask if they want to select a date in the future"""
        POPUP.show_custom_popup(
            header="Task is in the past!",
            field_text=f"{self.task_manager.selected_date} at {self.task_manager.selected_time.strftime(DM.DATE.SELECTED_TIME)}",
            extra_info="Please select date in the future.",
            confirm_text="Confirm",
            on_confirm=lambda: None,
            on_cancel=lambda: None
        )
    
    def edit_existing_task(self, instance) -> None:
        """
        Edit the existing task
        Called when the user selects a date for an existing task.
        """
        ##
        ## NOT BY TIMESTAMP !
        date = datetime.combine(self.task_manager.selected_date, self.task_manager.selected_time)
        task = self.task_manager.get_task_by_timestamp(date)
        self.app.get_screen(DM.SCREEN.NEW_TASK).load_task_data(task=task)
        self.navigation_manager.navigate_to(DM.SCREEN.NEW_TASK)
    
    def init_date_values(self) -> None:
        """Initialize date values"""
        if not self.task_manager.selected_date:
            self.task_manager.selected_date = datetime.now().date()
        
        self.current_month = self.task_manager.selected_date.month
        self.current_year = self.task_manager.selected_date.year
    
    def init_time_values(self) -> None:
        """Initialize time values"""
        if not self.task_manager.selected_time:
            self.task_manager.selected_time = datetime.now().time()

        self.time_input.set_text(self.task_manager.selected_time)
    
    def init_calendar_labels(self) -> None:
        """Initialize calendar labels"""
        date_str = self.task_manager.selected_date.strftime(DM.DATE.CALENDAR_DAY)
        self.selected_date_label.set_text(f"{date_str}")

        month_name = calendar.month_name[self.current_month]
        self.month_label.set_text(f"{month_name} {self.current_year}")

    def on_pre_enter(self) -> None:
        """Called when the screen is entered"""
        super().on_pre_enter()
        
        self.init_date_values()
        self.init_time_values()
        self.init_calendar_labels()

        self.update_calendar()
    
    def on_enter(self) -> None:
        """Called when the screen is entered"""
        pass
