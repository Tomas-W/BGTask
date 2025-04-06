import calendar
from datetime import datetime, date

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.label import Label
from kivy.app import App

from src.screens.base.base_screen import BaseScreen

from src.widgets.buttons import CustomConfirmButton, CustomCancelButton
from src.widgets.containers import (ScrollContainer, CustomButtonRow, Partition,
                                    CustomRow)
from src.widgets.labels import PartitionHeader
from src.widgets.fields import InputField
from .select_date_widgets import (DateTimeLabel, CalendarContainer,
                                  CalendarHeadersContainer, CalendarHeaderLabel,
                                  CalendarGrid)

from src.settings import COL, SIZE, SPACE, STATE, STYLE, SCREEN


class SelectDateScreen(BaseScreen):
    def __init__(self, navigation_manager, task_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager

        # Initialize current month/year for calendar view
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        # TopBar title
        self.top_bar.bar_title.set_text("Select Date")


        # Select month partition
        self.select_month_partition = Partition()
        # Select month row
        self.select_month_row = CustomButtonRow()
        # Previous month button
        self.prev_month_button = CustomConfirmButton(
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
        self.next_month_button = CustomConfirmButton(
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
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK))
        # Confirm button
        self.confirm_button = CustomConfirmButton(text="Confirm", width=2,
                                                  color_state=STATE.ACTIVE)
        self.confirm_button.bind(on_release=self.confirm_date_selection)
        # Apply confirmation partition
        self.confirmation_row.add_widget(self.cancel_button)
        self.confirmation_row.add_widget(self.confirm_button)
        self.confirmation_partition.add_widget(self.confirmation_row)
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add callback property
        self.callback = None
    
    def create_calendar_grid(self) -> None:
        """Create and populate the calendar grid"""
        self.calendar_container = CalendarContainer()

        # Day headers
        headers_container = CalendarHeadersContainer()
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            header_label = CalendarHeaderLabel(text=day)
            headers_container.add_widget(header_label)
        
        # Calendar grid
        self.calendar_grid = CalendarGrid()
        self.calendar_container.add_widget(headers_container)
        self.calendar_container.add_widget(self.calendar_grid)
        
        self.update_calendar()
        self.select_day_partition.add_widget(self.calendar_container)

    def update_calendar(self) -> None:
        """Update the calendar grid for the current month/year"""
        month_name = calendar.month_name[self.current_month]
        self.month_label.set_text(f"{month_name} {self.current_year}")
        
        # Clear day buttons
        for child in list(self.calendar_grid.children):
            self.calendar_grid.remove_widget(child)
        
        calendar.setfirstweekday(calendar.MONDAY)
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        # Extract necessary weeks
        if len(cal) > 5:
            last_week = cal[-1]
            if all(day == 0 for day in last_week):
                cal = cal[:-1] 
        
        # Add day buttons
        for week in cal:
            for day in week:
                if day == 0:
                    # Empty cell for days not in current month
                    empty_label = Label(
                        text="",
                        size_hint_y=None,
                        height=SIZE.HEADER_HEIGHT,
                    )
                    self.calendar_grid.add_widget(empty_label)
                else:
                    day_button = DateTimeLabel(
                        text=str(day),
                    )
                    
                    # Highlight the selected date if it exists
                    if (self.task_manager.selected_date and
                        day == self.task_manager.selected_date.day and 
                        self.current_month == self.task_manager.selected_date.month and 
                        self.current_year == self.task_manager.selected_date.year):
                        with day_button.canvas.before:
                            Color(*COL.FIELD_ACTIVE)
                            RoundedRectangle(pos=day_button.pos,
                                           size=day_button.size,
                                           radius=[STYLE.RADIUS_S])
                        day_button.color = COL.TEXT
                        day_button.set_bold(True)
                        day_button.bind(pos=self.update_selected_day, 
                                       size=self.update_selected_day)
                    
                    day_button.bind(on_release=lambda btn, d=day: self.select_day(d))
                    self.calendar_grid.add_widget(day_button)
    
    def update_selected_day(self, instance, value) -> None:
        """
        Add background, text color and bold to the selected day
        """
        if not self.task_manager.selected_date:
            return
            
        for child in self.calendar_grid.children:
            if isinstance(child, DateTimeLabel) and child.text == str(self.task_manager.selected_date.day):
                for instr in child.canvas.before.children:
                    if isinstance(instr, Rectangle):
                        instr.pos = child.pos
                        instr.size = child.size
    
    def select_day(self, day: int) -> None:
        """Handle day selection"""
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
    
    def go_to_prev_month(self, instance) -> None:
        """Go to previous month"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()
    
    def go_to_next_month(self, instance) -> None:
        """Go to next month"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()

    def confirm_date_selection(self, instance) -> None:
        """Return to new task screen, passing selected date if confirm was pressed"""
        if instance == self.confirm_button:
            hours_input: str = self.hours_input.text_input.text.strip()
            minutes_input: str = self.minutes_input.text_input.text.strip()

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

            if not valid:
                return

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
                return

            # Handle callback
            if self.callback:
                self.callback(self.task_manager.selected_date, self.task_manager.selected_time)

        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)
    
    def validate_hours(self, instance, value) -> None:
        """Allow any input during typing"""
        if len(value) > 2:
            instance.text = instance.text[:2]

    def validate_minutes(self, instance, value) -> None:
        """Allow any input during typing"""
        if len(value) > 2:
            instance.text = instance.text[:2]

    def on_pre_enter(self) -> None:
        """Called when the screen is entered"""
        super().on_pre_enter()
        
        # If no date/time is selected, initialize with current values
        if not self.task_manager.selected_date:
            self.task_manager.selected_date = datetime.now().date()
            
        if not self.task_manager.selected_time:
            self.task_manager.selected_time = datetime.now().time()
            
        # Set current month/year based on selected date
        self.current_month = self.task_manager.selected_date.month
        self.current_year = self.task_manager.selected_date.year
        
        # Update hours and minutes input with selected time values
        self.hours_input.set_text(self.task_manager.selected_time.strftime("%H"))
        self.minutes_input.set_text(self.task_manager.selected_time.strftime("%M"))
        
        # Update date label with selected date
        date_str = self.task_manager.selected_date.strftime("%A %d")
        self.selected_date_label.set_text(f"{date_str}")
        
        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.set_text(f"{month_name} {self.current_year}")
        
        # Update calendar to show selected date
        self.update_calendar()
    
    def on_enter(self) -> None:
        """Called when the screen is entered"""
        pass
