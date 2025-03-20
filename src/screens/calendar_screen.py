from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle
from datetime import datetime, date, time
import calendar

from src.utils.buttons import TopBar, CustomButton
from src.utils.containers import BaseLayout, ScrollContainer, ButtonRow, Partition
from src.utils.labels import PartitionHeader
from src.utils.misc import Spacer
from src.settings import COL, FONT, SCREEN, SPACE, SIZE

# Create a DateTimeLabel for day selection (copied from calendar.py)
class DateTimeLabel(ButtonBehavior, Label):
    """Label that behaves like a button"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = dp(FONT.DEFAULT)
        self.color = COL.TEXT
        self.size_hint_y = None
        self.height = dp(SIZE.HEADER_HEIGHT)
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self.setter("text_size"))


class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Initialize date and time
        self.selected_date = datetime.now().date()
        self.selected_time = datetime.now().time()
        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year

        # Top bar
        self.top_bar = TopBar(text="Select date", button=False)
        self.layout.add_widget(self.top_bar)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)
        # self.scroll_container.container.spacing = dp(SPACE.SPACE_Y_XL)

        # Select month partition with background
        self.select_month_partition = Partition()
        self.select_month_partition.spacing = dp(SPACE.SPACE_Y_XS)
        # with self.select_month_partition.canvas.before:
        #     Color(*COL.FIELD_ACTIVE)
        #     self.select_month_rect = Rectangle()
        #     self.select_month_partition.bind(pos=self._update_month_rect, 
        #                                    size=self._update_month_rect)
        
        # Month button row
        self.month_button_row = ButtonRow()
        
        # Previous month button
        self.prev_month_button = CustomButton(
            text="<",
            width=0.6,
            color_state="active"
        )
        self.prev_month_button.bind(on_press=self.go_to_prev_month)
        
        # Select month label - update with current month/year
        month_name = calendar.month_name[self.current_month]
        self.month_label = PartitionHeader(text=f"{month_name} {self.current_year}")
        
        # Next month button
        self.next_month_button = CustomButton(
            text=">",
            width=0.6,
            color_state="active"
        )
        self.next_month_button.bind(on_press=self.go_to_next_month)

        # Apply month partition
        self.month_button_row.add_widget(self.prev_month_button)
        self.month_button_row.add_widget(self.month_label)
        self.month_button_row.add_widget(self.next_month_button)
        self.select_month_partition.add_widget(self.month_button_row)
        date_str = self.selected_date.strftime("%A %d")
        time_str = self.selected_time.strftime("%H:%M")
        self.selected_date_label = PartitionHeader(text=f"{date_str} at {time_str}")
        self.select_month_partition.add_widget(self.selected_date_label)
        self.scroll_container.container.add_widget(self.select_month_partition)

        # Calendar partition with background
        self.calendar_partition = Partition()
        # self.calendar_partition.spacing = dp(SPACE.SPACE_Y_XS)
        # with self.calendar_partition.canvas.before:
        #     Color(*COL.FIELD_ACTIVE)
        #     self.calendar_rect = Rectangle()
        #     self.calendar_partition.bind(pos=self._update_calendar_rect, 
        #                                size=self._update_calendar_rect)
        
        # date_str = self.selected_date.strftime("%A %d")
        # time_str = self.selected_time.strftime("%H:%M")
        # self.selected_date_label = PartitionHeader(text=f"{date_str} at {time_str}")
        # self.calendar_partition.add_widget(self.selected_date_label)
        
        # Create and add calendar grid
        self.create_calendar_grid()

        # Apply calendar partition to the main container
        self.scroll_container.container.add_widget(self.calendar_partition)
        
        # Confirmation partition with background
        self.confirmation_partition = Partition()
        # with self.confirmation_partition.canvas.before:
        #     Color(*COL.FIELD_ACTIVE)
        #     self.confirm_rect = Rectangle()
        #     self.confirmation_partition.bind(pos=self._update_confirm_rect, 
        #                                    size=self._update_confirm_rect)

        # Confirm button row
        self.confirm_button_row = ButtonRow()
        # Cancel button
        self.cancel_button = CustomButton(
            text="Cancel",
            width=2,
            color_state="inactive"
        )
        self.cancel_button.bind(on_press=self.go_to_new_task_screen)
        # Confirm button
        self.confirm_button = CustomButton(
            text="Confirm",
            width=2,
            color_state="active"
        )
        self.confirm_button.bind(on_press=self.go_to_new_task_screen)

        # Apply confirmation partition
        self.confirm_button_row.add_widget(self.cancel_button)
        self.confirm_button_row.add_widget(self.confirm_button)
        self.confirmation_partition.add_widget(self.confirm_button_row)
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Apply layout
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        # Add callback property
        self.callback = None

    def create_calendar_grid(self):
        """Create and populate the calendar grid"""
        # Create a container for the calendar with reduced height
        self.calendar_container = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(SIZE.CALENDAR_HEIGHT),
            spacing=dp(4)
        )
        
        # Headers container
        headers_container = GridLayout(
            cols=7,
            spacing=dp(1),
            size_hint=(1, None),
            height=dp(SIZE.HEADER_HEIGHT)
        )
        
        # Day of week headers starting with Monday
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            header_label = Label(
                text=day,
                bold=True,
                color=COL.TEXT,
                font_size=dp(FONT.CALENDAR),
                size_hint_y=None,
                height=dp(FONT.CALENDAR)
            )
            headers_container.add_widget(header_label)
        
        # Calendar grid with reduced height and spacing
        self.calendar_grid = GridLayout(
            cols=7,
            spacing=dp(1),
            size_hint=(1, None),
            height=dp(SIZE.CALENDAR_HEIGHT)
        )
        
        self.calendar_container.add_widget(headers_container)
        self.calendar_container.add_widget(self.calendar_grid)
        
        # Initialize calendar with dates
        self.update_calendar()
        
        # Add the container to the calendar partition with reduced spacing
        self.calendar_partition.spacing = dp(SPACE.SPACE_Y_XS)
        self.calendar_partition.add_widget(self.calendar_container)

    def update_calendar(self):
        """Update the calendar grid for the current month/year"""
        # Update month/year label
        month_name = calendar.month_name[self.current_month]
        self.month_label.text = f"{month_name} {self.current_year}"
        
        # Clear existing day buttons
        for child in list(self.calendar_grid.children):
            self.calendar_grid.remove_widget(child)
        
        # Set calendar to start week on Monday
        calendar.setfirstweekday(calendar.MONDAY)
        
        # Get calendar for current month
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        # Only show up to 5 weeks
        if len(cal) > 5:
            # Check if the last week has any days in the current month
            last_week = cal[-1]
            if all(day == 0 for day in last_week):
                cal = cal[:-1]  # Remove the last week if it's empty
        
        # Add day buttons
        for week in cal:
            for day in week:
                if day == 0:
                    # Empty cell for days not in current month
                    empty_label = Label(
                        text="",
                        size_hint_y=None,
                        height=dp(SIZE.HEADER_HEIGHT * 0.8)
                    )
                    self.calendar_grid.add_widget(empty_label)
                else:
                    day_button = DateTimeLabel(
                        text=str(day),
                        size_hint_y=None,
                        height=dp(SIZE.HEADER_HEIGHT * 0.8)
                    )
                    
                    # Highlight the selected date
                    if (day == self.selected_date.day and 
                        self.current_month == self.selected_date.month and 
                        self.current_year == self.selected_date.year):
                        with day_button.canvas.before:
                            Color(*COL.FIELD_ACTIVE)
                            Rectangle(pos=day_button.pos, size=day_button.size)
                        day_button.color = COL.WHITE
                        day_button.bind(pos=self.update_selected_day, 
                                       size=self.update_selected_day)
                    
                    day_button.bind(on_press=lambda btn, d=day: self.select_day(d))
                    self.calendar_grid.add_widget(day_button)
    
    def update_selected_day(self, instance, value):
        """Update the background rectangle for the selected day"""
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
            self.update_calendar()  # Refresh calendar to highlight the selected day
            
            # Update selected date label
            date_str = self.selected_date.strftime("%A %d")
            time_str = self.selected_time.strftime("%H:%M")
            self.selected_date_label.text = f"{date_str} at {time_str}"
        except ValueError:
            pass  # Invalid date
    
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
    
    def set_callback(self, callback):
        """Set the callback function to be called when date is confirmed"""
        self.callback = callback

    def go_to_new_task_screen(self, instance):
        """Return to new task screen, passing selected date if confirm was pressed"""
        if instance == self.confirm_button:
            # Call the callback with selected date and time if it exists
            if self.callback:
                self.callback(self.selected_date, self.selected_time)
        
        self.manager.current = SCREEN.NEW_TASK

    def _update_month_rect(self, instance, value):
        self.select_month_rect.pos = instance.pos
        self.select_month_rect.size = instance.size

    def _update_calendar_rect(self, instance, value):
        self.calendar_rect.pos = instance.pos
        self.calendar_rect.size = instance.size

    def _update_confirm_rect(self, instance, value):
        self.confirm_rect.pos = instance.pos
        self.confirm_rect.size = instance.size
