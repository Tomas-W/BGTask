import calendar
from typing import TYPE_CHECKING

from datetime import datetime, date

from src.screens.base.base_screen import BaseScreen
from .select_date_utils import SelectDateUtils

from src.widgets.buttons import ConfirmButton, CancelButton
from src.widgets.containers import CustomButtonRow, Partition, CustomRow
from src.widgets.labels import PartitionHeader
from src.widgets.fields import InputField

from src.widgets.popups import POPUP

from src.utils.logger import logger

from src.settings import SPACE, STATE, SCREEN


if TYPE_CHECKING:
    from src.managers.tasks.task_manager import TaskManager
    from src.managers.navigation_manager import NavigationManager


class SelectDateScreen(BaseScreen, SelectDateUtils):
    def __init__(self, navigation_manager: "NavigationManager",
                 task_manager: "TaskManager", **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager: NavigationManager = navigation_manager
        self.task_manager: TaskManager = task_manager

        # Initialize current month/year for calendar view
        self.current_month: int = datetime.now().month
        self.current_year: int = datetime.now().year
        
        # TopBar title
        self.top_bar.bar_title.set_text("Select Date")

        # Select month partition
        self.select_month_partition = Partition()
        # Select month row
        self.select_month_row = CustomButtonRow()
        # Previous month button
        self.prev_month_button = ConfirmButton(
            text="<",
            width=0.6,
            symbol=True,
            color_state=STATE.ACTIVE,
        )
        self.prev_month_button.bind(on_release=self.go_to_prev_month)
        # Select month label
        month_name = calendar.month_name[self.current_month]
        self.month_label = PartitionHeader(text=f"{month_name} {self.current_year}")
        # Next month button
        self.next_month_button = ConfirmButton(
            text=">",
            width=0.6,
            symbol=True,
            color_state=STATE.ACTIVE,
        )
        self.next_month_button.bind(on_release=self.go_to_next_month)
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
        # Hours input
        self.hours_input = InputField()
        self.hours_input.text_input.input_filter = "int"
        self.hours_input.text_input.bind(text=self.validate_hours)
        # Colon separator
        colon_label = PartitionHeader(text=":")
        colon_label.size_hint_x = 0.2
        # Minutes input
        self.minutes_input = InputField()
        self.minutes_input.text_input.input_filter = "int"
        self.minutes_input.text_input.bind(text=self.validate_minutes)
        # Apply time row
        self.select_time_row.add_widget(self.hours_input)
        self.select_time_row.add_widget(colon_label)
        self.select_time_row.add_widget(self.minutes_input)
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
        self.cancel_button.bind(on_release=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK))
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
                self.hours_input.set_text(now.strftime("%H"))
                self.minutes_input.set_text(now.strftime("%M"))
                
            # Highlight selected day
            self.update_calendar()
            
            # Update date label
            date_str = selected_date.strftime("%A %d")
            self.selected_date_label.set_text(f"{date_str}")

        except ValueError:
            pass
    
    def validate_time(self, hours_input: str, minutes_input: str) -> bool:
        """Validate hours and minutes input by checking type and range"""
        valid = True
        if hours_input and (not hours_input.isdigit() or int(hours_input) > 23 or int(hours_input) < 0):
            self.hours_input.show_error_border()
            valid = False
        else:
            self.hours_input.hide_border()

        if minutes_input and (not minutes_input.isdigit() or int(minutes_input) > 59 or int(minutes_input) < 0):
            self.minutes_input.show_error_border()
            valid = False
        else:
            self.minutes_input.hide_border()

        return valid
    
    def update_task_manager_time(self, hours_input: str, minutes_input: str) -> None:
        """
        Update the task manager's selected time after user selection.
        """
        # Ensure we have a selected date
        if not self.task_manager.selected_date:
            self.task_manager.selected_date = datetime.now().date()
            
        # Update selected time in task_manager
        try:
            current_time = self.task_manager.selected_time or datetime.now().time()
            updated_time = current_time.replace(
                hour=int(hours_input) if hours_input else current_time.hour,
                minute=int(minutes_input) if minutes_input else current_time.minute
            )
            self.task_manager.selected_time = updated_time
        except ValueError:
            return False
        
        return True
    
    def check_date_is_taken(self) -> bool:
        """
        Check if the date is taken by an existing task.
        If so, show a popup to the user to ask if they want to edit the existing task or
         select a different date.
        """
        date = datetime.combine(self.task_manager.selected_date, self.task_manager.selected_time)
        if self.task_manager.date_is_taken(date):
            POPUP.show_custom_popup(
                header="Existing task found for:",
                field_text=f"{self.task_manager.selected_date} at {self.task_manager.selected_time.strftime('%H:%M')}",
                extra_info="Cancel to resume selection\nEdit to update existing task",
                confirm_text="Edit",
                on_confirm=self.edit_existing_task,
                on_cancel=lambda: None
            )
            return True
        
        return False
    
    def confirm_date_selection(self, instance) -> None:
        """Return to new task screen, passing selected date"""
        hours_input: str = self.hours_input.text_input.text.strip()
        minutes_input: str = self.minutes_input.text_input.text.strip()
        if not self.validate_time(hours_input, minutes_input):
            return
        
        if not self.update_task_manager_time(hours_input, minutes_input):
            return

        if self.check_date_is_taken():
            return
        
        # Handle callback
        if self.callback:
            self.callback(self.task_manager.selected_date, self.task_manager.selected_time)

        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)
    
    def edit_existing_task(self, instance) -> None:
        """
        Edit the existing task
        Called when the user selects a date for an existing task.
        """
        date = datetime.combine(self.task_manager.selected_date, self.task_manager.selected_time)
        task = self.task_manager.get_task_by_timestamp(date)
        self.task_manager.dispatch("on_task_edit_load_task_data", task=task)
        self.navigation_manager.navigate_to(SCREEN.NEW_TASK)
    
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

        self.hours_input.set_text(self.task_manager.selected_time.strftime("%H"))
        self.minutes_input.set_text(self.task_manager.selected_time.strftime("%M"))
    
    def init_calendar_labels(self) -> None:
        """Initialize calendar labels"""
        date_str = self.task_manager.selected_date.strftime("%A %d")
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
