from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from datetime import datetime, date, time, timedelta
import calendar

from src.settings import COL, SPACE, SIZE, STYLE, FONT

class DateTimeButton(Button):
    """Button for date and time selection"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COL.BG
        self.color = COL.WHITE
        self.size_hint = (1, None)
        self.height = dp(SIZE.BUTTON_HEIGHT)
        self.font_size = dp(FONT.DEFAULT)


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


class DateTimePickerPopup(Popup):
    """Custom popup with calendar and time picker"""
    def __init__(self, selected_date=None, selected_time=None, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Select Date & Time"
        self.size_hint = (0.9, 0.9)
        self.callback = callback
        
        # Set default values if not provided
        self.selected_date = selected_date if selected_date else datetime.now().date()
        self.selected_time = selected_time if selected_time else datetime.now().time()
        
        # Set up content
        self.content = BoxLayout(orientation="vertical", spacing=dp(0), padding=dp(SPACE.FIELD_PADDING_X))
        
        # Calendar header
        self.calendar_header = BoxLayout(size_hint=(1, None), height=dp(SIZE.CALENDAR_HEADER_HEIGHT))
        
        # Previous month button
        self.prev_month_btn = Button(
            text="<",
            background_color=COL.BUTTON_INACTIVE,
            color=COL.WHITE,
            size_hint=(0.2, 1)
        )
        self.prev_month_btn.bind(on_press=self.go_to_prev_month)
        
        # Month/year label
        self.month_year = Label(
            size_hint=(0.6, 1),
            color=COL.TEXT,
            font_size=dp(FONT.CALENDAR),
            bold=True
        )
        
        # Next month button
        self.next_month_btn = Button(
            text=">",
            background_color=COL.BUTTON_INACTIVE,
            color=COL.WHITE,
            size_hint=(0.2, 1)
        )
        self.next_month_btn.bind(on_press=self.go_to_next_month)
        
        self.calendar_header.add_widget(self.prev_month_btn)
        self.calendar_header.add_widget(self.month_year)
        self.calendar_header.add_widget(self.next_month_btn)
        
        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, spacing=dp(2), size_hint=(1, None), height=dp(SIZE.CALENDAR_HEIGHT))
        
        # Day of week headers
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            self.calendar_grid.add_widget(
                Label(
                    text=day,
                    bold=True,
                    color=COL.TEXT
                )
            )
        
        # Calendar days (will be populated in update_calendar)
        self.day_buttons = []
        
        # Time picker
        self.time_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(SIZE.BUTTON_HEIGHT),
            spacing=dp(0)
        )
        
        # Hour picker
        self.hour_label = Label(
            text="Hour:",
            size_hint=(0.2, 1),
            color=COL.TEXT
        )
        
        self.hour_input = TextInput(
            text=str(self.selected_time.hour).zfill(2),
            multiline=False,
            input_filter="int",
            size_hint=(0.2, 1),
            font_size=dp(FONT.HEADER),
            halign="center"
        )
        
        # Minute picker
        self.minute_label = Label(
            text="Minute:",
            size_hint=(0.2, 1),
            color=COL.TEXT
        )
        
        self.minute_input = TextInput(
            text=str(self.selected_time.minute).zfill(2),
            multiline=False,
            input_filter="int",
            size_hint=(0.2, 1),
            font_size=dp(FONT.HEADER),
            halign="center"
        )
        
        self.time_layout.add_widget(self.hour_label)
        self.time_layout.add_widget(self.hour_input)
        self.time_layout.add_widget(self.minute_label)
        self.time_layout.add_widget(self.minute_input)
        
        # Action buttons
        self.buttons_layout = BoxLayout(
            size_hint=(1, None),
            height=dp(SIZE.BUTTON_HEIGHT),
            spacing=dp(0)
        )
        
        self.cancel_btn = Button(
            text="Cancel",
            background_color=COL.BUTTON_INACTIVE,
            color=COL.WHITE,
            size_hint=(0.5, 1)
        )
        self.cancel_btn.bind(on_press=self.dismiss)
        
        self.ok_btn = Button(
            text="OK",
            background_color=COL.BUTTON_ACTIVE,
            color=COL.WHITE,
            size_hint=(0.5, 1)
        )
        self.ok_btn.bind(on_press=self.confirm_selection)
        
        self.buttons_layout.add_widget(self.cancel_btn)
        self.buttons_layout.add_widget(self.ok_btn)
        
        # Add all components to content
        self.content.add_widget(self.calendar_header)
        self.content.add_widget(self.calendar_grid)
        self.content.add_widget(self.time_layout)
        self.content.add_widget(self.buttons_layout)
        
        # Initialize calendar
        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year
        self.update_calendar()
    
    def update_calendar(self):
        """Update the calendar grid for the current month/year"""
        # Update month/year label
        month_name = calendar.month_name[self.current_month]
        self.month_year.text = f"{month_name} {self.current_year}"
        
        # Clear existing day buttons
        for child in list(self.calendar_grid.children)[:-7]:  # Keep day headers
            self.calendar_grid.remove_widget(child)
        
        # Get calendar for current month
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        # Add day buttons
        for week in cal:
            for day in week:
                if day == 0:
                    # Empty cell for days not in current month
                    self.calendar_grid.add_widget(Label(text=""))
                else:
                    day_button = DateTimeLabel(text=str(day))
                    
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
    
    def confirm_selection(self, instance):
        """Confirm the date and time selection"""
        try:
            # Get hour and minute from input fields
            hour = int(self.hour_input.text) % 24
            minute = int(self.minute_input.text) % 60
            
            # Create time object
            self.selected_time = time(hour, minute)
            
            # Call the callback function with selected date and time
            if self.callback:
                self.callback(self.selected_date, self.selected_time)
            
            self.dismiss()
        except ValueError:
            # Handle invalid time input
            self.hour_input.text = "00"
            self.minute_input.text = "00"
