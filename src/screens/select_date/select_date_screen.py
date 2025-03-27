import calendar

from datetime import datetime, date

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from src.screens.base.base_screen import BaseScreen  # type: ignore

from src.utils.bars import TopBarClosed, TopBarExpanded
from src.utils.buttons import CustomButton
from src.utils.containers import BaseLayout, ScrollContainer, CustomButtonRow, Partition, CustomRow
from src.utils.labels import PartitionHeader
from src.utils.fields import InputField
from .select_date_widgets import DateTimeLabel, CalendarContainer, CalendarHeadersContainer, CalendarHeaderLabel, CalendarGrid

from src.settings import COL, SIZE, SPACE, STATE, STYLE, SCREEN


class SelectDateScreen(BaseScreen):
    def __init__(self, navigation_manager, task_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        
        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Initialize date and time
        self.selected_date = datetime.now().date()
        self.selected_time = datetime.now().time()
        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year

        # Top bar
        self.top_bar = TopBarClosed(
            bar_title="Select Date",
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK),
            options_callback=lambda instance: self.switch_top_bar(),
        )
        # Top bar with expanded options
        self.top_bar_expanded = TopBarExpanded(
            back_callback=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK),
            options_callback=lambda instance: self.switch_top_bar(),
            settings_callback=lambda instance: self.navigation_manager.navigate_to(SCREEN.SETTINGS),
            exit_callback=lambda instance: self.navigation_manager.exit_app(),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Select month partition
        self.select_month_partition = Partition()
        # Select month row
        self.select_month_row = CustomButtonRow()
        # Previous month button
        self.prev_month_button = CustomButton(
            text="<",
            width=0.6,
            symbol=True,
        )
        self.prev_month_button.bind(on_press=self.go_to_prev_month)
        # Select month label
        month_name = calendar.month_name[self.current_month]
        self.month_label = PartitionHeader(text=f"{month_name} {self.current_year}")
        # Next month button
        self.next_month_button = CustomButton(
            text=">",
            width=0.6,
            symbol=True,
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
        date_str = self.selected_date.strftime("%A %d")
        self.selected_date_label = PartitionHeader(text=f"{date_str}")
        self.select_time_partition.add_widget(self.selected_date_label)
        # Time selection row
        self.select_time_row = CustomRow()
        # Hours input
        self.hours_input = InputField()
        self.hours_input.set_text(self.selected_time.strftime("%H"))
        self.hours_input.text_input.input_filter = "int"
        self.hours_input.text_input.bind(text=self.validate_hours)
        # Colon separator
        colon_label = PartitionHeader(text=":")
        colon_label.size_hint_x = 0.2
        # Minutes input
        self.minutes_input = InputField()
        self.minutes_input.set_text(self.selected_time.strftime("%M"))
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
        self.cancel_button = CustomButton(
            text="Cancel",
            width=2,
            color_state=STATE.INACTIVE
        )
        self.cancel_button.bind(on_press=lambda instance: self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK))
        # Confirm button
        self.confirm_button = CustomButton(
            text="Confirm",
            width=2,
        )
        self.confirm_button.bind(on_press=self.confirm_date_selection)
        # Apply confirmation partition
        self.confirmation_row.add_widget(self.cancel_button)
        self.confirmation_row.add_widget(self.confirm_button)
        self.confirmation_partition.add_widget(self.confirmation_row)
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        # Add callback property
        self.callback = None
    
    def create_calendar_grid(self):
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

    def update_calendar(self):
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
                    
                    # Highlight the selected date
                    if (day == self.selected_date.day and 
                        self.current_month == self.selected_date.month and 
                        self.current_year == self.selected_date.year):
                        with day_button.canvas.before:
                            Color(*COL.FIELD_ACTIVE)
                            RoundedRectangle(pos=day_button.pos,
                                           size=day_button.size,
                                           radius=[STYLE.RADIUS_S])
                        day_button.color = COL.TEXT
                        day_button.set_bold(True)
                        day_button.bind(pos=self.update_selected_day, 
                                       size=self.update_selected_day)
                    
                    day_button.bind(on_press=lambda btn, d=day: self.select_day(d))
                    self.calendar_grid.add_widget(day_button)
    
    def update_selected_day(self, instance, value):
        """
        Add background, text color and bold to the selected day
        """
        for child in self.calendar_grid.children:
            if isinstance(child, DateTimeLabel) and child.text == str(self.selected_date.day):
                for instr in child.canvas.before.children:
                    if isinstance(instr, Rectangle):
                        instr.pos = child.pos
                        instr.size = child.size
    
    def select_day(self, day):
        """Handle day selection"""
        try:
            self.selected_date = date(self.current_year, self.current_month, day)
            # Highlight selected day
            self.update_calendar()
            
            # Update date label
            date_str = self.selected_date.strftime("%A %d")
            self.selected_date_label.set_text(f"{date_str}")
        except ValueError:
            pass
    
    def go_to_prev_month(self, instance):
        """Go to previous month"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()
    
    def go_to_next_month(self, instance):
        """Go to next month"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()

    def confirm_date_selection(self, instance):
        """Return to new task screen, passing selected date if confirm was pressed"""
        if instance == self.confirm_button:
            hours_input = self.hours_input.text_input.text.strip()
            minutes_input = self.minutes_input.text_input.text.strip()

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

            # Update selected time
            try:
                self.selected_time = self.selected_time.replace(
                    hour=int(hours_input) if hours_input else self.selected_time.hour,
                    minute=int(minutes_input) if minutes_input else self.selected_time.minute
                )
            except ValueError:
                return

            # Handle callback
            if self.callback:
                self.callback(self.selected_date, self.selected_time)

        self.navigation_manager.navigate_back_to(SCREEN.NEW_TASK)
    
    def validate_hours(self, instance, value):
        """Allow any input during typing"""
        if len(value) > 2:
            instance.set_text(instance.text[:2])

    def validate_minutes(self, instance, value):
        """Allow any input during typing"""
        if len(value) > 2:
            instance.set_text(instance.text[:2])

    def on_pre_enter(self):
        """Called when the screen is entered"""
        super().on_pre_enter()
        
        # Update hours and minutes input with selected time values
        if hasattr(self, "selected_time"):
            self.hours_input.set_text(self.selected_time.strftime("%H"))
            self.minutes_input.set_text(self.selected_time.strftime("%M"))
        
        # Update date label with selected date
        if hasattr(self, "selected_date"):
            date_str = self.selected_date.strftime("%A %d")
            self.selected_date_label.set_text(f"{date_str}")
        
        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.set_text(f"{month_name} {self.current_year}")
        
        # Apply styling to selected date
        for child in self.calendar_grid.children:
            if isinstance(child, DateTimeLabel):
                if child.text == str(self.selected_date.day):
                    child.color = COL.TEXT
                    child.set_bold(True)
                else:
                    child.color = COL.TEXT_GREY
                    child.set_bold(False)
    
    def on_enter(self):
        """Called when the screen is entered"""
        pass
