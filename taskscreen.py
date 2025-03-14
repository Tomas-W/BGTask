from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, NumericProperty
from datetime import datetime, date, time, timedelta
import calendar
import settings

class DateTimeButton(Button):
    """Button for date and time selection"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = settings.BLUE
        self.color = settings.WHITE
        self.size_hint = (1, None)
        self.height = dp(settings.BUTTON_HEIGHT)
        self.font_size = dp(settings.DEFAULT_FONT_SIZE)

class DateTimeLabel(ButtonBehavior, Label):
    """Label that behaves like a button"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = dp(settings.DEFAULT_FONT_SIZE)
        self.color = settings.TEXT_COLOR
        self.size_hint_y = None
        self.height = dp(settings.HEADER_HEIGHT)
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
        self.content = BoxLayout(orientation="vertical", spacing=dp(0), padding=dp(settings.FIELD_PADDING_X))
        
        # Calendar header
        self.calendar_header = BoxLayout(size_hint=(1, None), height=dp(settings.CALENDAR_HEADER_HEIGHT))
        
        # Previous month button
        self.prev_month_btn = Button(
            text="<",
            background_color=settings.GREY,
            color=settings.WHITE,
            size_hint=(0.2, 1)
        )
        self.prev_month_btn.bind(on_press=self.go_to_prev_month)
        
        # Month/year label
        self.month_year = Label(
            size_hint=(0.6, 1),
            color=settings.TEXT_COLOR,
            font_size=dp(settings.CALENDAR_FONT_SIZE),
            bold=True
        )
        
        # Next month button
        self.next_month_btn = Button(
            text=">",
            background_color=settings.GREY,
            color=settings.WHITE,
            size_hint=(0.2, 1)
        )
        self.next_month_btn.bind(on_press=self.go_to_next_month)
        
        self.calendar_header.add_widget(self.prev_month_btn)
        self.calendar_header.add_widget(self.month_year)
        self.calendar_header.add_widget(self.next_month_btn)
        
        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, spacing=dp(2), size_hint=(1, None), height=dp(settings.CALENDAR_HEIGHT))
        
        # Day of week headers
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            self.calendar_grid.add_widget(
                Label(
                    text=day,
                    bold=True,
                    color=settings.TEXT_COLOR
                )
            )
        
        # Calendar days (will be populated in update_calendar)
        self.day_buttons = []
        
        # Time picker
        self.time_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(settings.BUTTON_HEIGHT),
            spacing=dp(0)
        )
        
        # Hour picker
        self.hour_label = Label(
            text="Hour:",
            size_hint=(0.2, 1),
            color=settings.TEXT_COLOR
        )
        
        self.hour_input = TextInput(
            text=str(self.selected_time.hour).zfill(2),
            multiline=False,
            input_filter="int",
            size_hint=(0.2, 1),
            font_size=dp(settings.HEADER_FONT_SIZE),
            halign="center"
        )
        
        # Minute picker
        self.minute_label = Label(
            text="Minute:",
            size_hint=(0.2, 1),
            color=settings.TEXT_COLOR
        )
        
        self.minute_input = TextInput(
            text=str(self.selected_time.minute).zfill(2),
            multiline=False,
            input_filter="int",
            size_hint=(0.2, 1),
            font_size=dp(settings.HEADER_FONT_SIZE),
            halign="center"
        )
        
        self.time_layout.add_widget(self.hour_label)
        self.time_layout.add_widget(self.hour_input)
        self.time_layout.add_widget(self.minute_label)
        self.time_layout.add_widget(self.minute_input)
        
        # Action buttons
        self.buttons_layout = BoxLayout(
            size_hint=(1, None),
            height=dp(settings.BUTTON_HEIGHT),
            spacing=dp(0)
        )
        
        self.cancel_btn = Button(
            text="Cancel",
            background_color=settings.GREY,
            color=settings.WHITE,
            size_hint=(0.5, 1)
        )
        self.cancel_btn.bind(on_press=self.dismiss)
        
        self.ok_btn = Button(
            text="OK",
            background_color=settings.BLUE,
            color=settings.WHITE,
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
                            Color(*settings.BLUE)
                            Rectangle(pos=day_button.pos, size=day_button.size)
                        day_button.color = settings.WHITE
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


class TaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Root layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Top bar with title and cancel button
        self.top_bar = BoxLayout(
            size_hint=(1, None),
            height=dp(settings.NAV_HEIGHT),
            padding=[dp(0), 0, dp(0), 0]
        )
        
        # Top bar background
        with self.top_bar.canvas.before:
            Color(*settings.DARK_BLUE)
            self.rect = Rectangle(pos=self.top_bar.pos, size=self.top_bar.size)
            self.top_bar.bind(pos=self.update_rect, size=self.update_rect)
        
        # Title
        title_label = Label(
            text="New Task",
            bold=True,
            color=settings.WHITE,
            size_hint=(0.7, 1),
            font_size=dp(settings.HEADER_FONT_SIZE)
        )
        
        # Cancel button
        self.cancel_button = Button(
            text="Cancel",
            background_color=(0, 0, 0, 0),
            color=settings.WHITE,
            size_hint=(0.3, 1),
            font_size=dp(settings.DEFAULT_FONT_SIZE)
        )
        self.cancel_button.bind(on_press=self.cancel_task)
        
        self.top_bar.add_widget(title_label)
        self.top_bar.add_widget(self.cancel_button)
        
        # Content area
        self.content_layout = BoxLayout(
            orientation="vertical",
            padding=[dp(settings.SCREEN_PADDING_X), dp(0),
                     dp(settings.SCREEN_PADDING_X), dp(0)],
            spacing=dp(0)
        )
        
        # Date and time selection
        self.datetime_label = Label(
            text="Date & Time:",
            size_hint=(1, None),
            height=dp(settings.HEADER_HEIGHT),
            halign="left",
            color=settings.TEXT_COLOR,
            font_size=dp(settings.DEFAULT_FONT_SIZE),
            bold=True,
            padding=[dp(settings.FIELD_PADDING_X), 0]
        )
        self.datetime_label.bind(size=self.datetime_label.setter("text_size"))
        
        # Date and time button
        self.datetime_button = DateTimeButton(text="Select Date & Time")
        self.datetime_button.bind(on_press=self.show_datetime_picker)
        
        # Task input
        self.task_label = Label(
            text="Task:",
            size_hint=(1, None),
            height=dp(settings.HEADER_HEIGHT),
            halign="left",
            color=settings.TEXT_COLOR,
            font_size=dp(settings.DEFAULT_FONT_SIZE),
            bold=True,
            padding=[dp(settings.FIELD_PADDING_X), 0]
        )
        self.task_label.bind(size=self.task_label.setter("text_size"))
        
        self.task_input = TextInput(
            hint_text="Enter your task here",
            size_hint=(1, None),
            height=dp(settings.BUTTON_HEIGHT * 3),  # Taller input for multiline text
            multiline=True,
            font_size=dp(settings.DEFAULT_FONT_SIZE),
            padding=[dp(settings.FIELD_PADDING_X), dp(settings.FIELD_PADDING_Y)]
        )
        
        # Save button
        self.save_button = Button(
            text="Save Task",
            background_color=settings.BLUE,
            color=settings.WHITE,
            size_hint=(1, None),
            height=dp(settings.BUTTON_HEIGHT)
        )
        self.save_button.bind(on_press=self.save_task)
        
        # Add widgets to content layout
        self.content_layout.add_widget(self.datetime_label)
        self.content_layout.add_widget(self.datetime_button)
        self.content_layout.add_widget(self.task_label)
        self.content_layout.add_widget(self.task_input)
        self.content_layout.add_widget(self.save_button)
        
        # Background color
        with self.layout.canvas.before:
            Color(*settings.BG_WHITE)
            self.bg_rect = Rectangle(pos=self.layout.pos, size=self.layout.size)
            self.layout.bind(pos=self.update_rect, size=self.update_rect)
        
        # Assemble the layout
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.content_layout)
        
        self.add_widget(self.layout)
        
        # Initialize datetime
        self.selected_date = datetime.now().date()
        self.selected_time = datetime.now().time()
        self.update_datetime_button()
    
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def update_datetime_button(self):
        """Update the datetime button text with the selected date and time"""
        date_str = self.selected_date.strftime("%A, %B %d, %Y")
        time_str = self.selected_time.strftime("%H:%M")
        self.datetime_button.text = f"Date & Time: {date_str} at {time_str}"
    
    def show_datetime_picker(self, instance):
        """Show the datetime picker popup"""
        popup = DateTimePickerPopup(
            selected_date=self.selected_date,
            selected_time=self.selected_time,
            callback=self.on_datetime_selected
        )
        popup.open()
    
    def on_datetime_selected(self, selected_date, selected_time):
        """Callback when date and time are selected in the popup"""
        self.selected_date = selected_date
        self.selected_time = selected_time
        self.update_datetime_button()
    
    def cancel_task(self, instance):
        """Cancel task creation and return to home screen"""
        self.reset_form()
        self.manager.current = "home"
    
    def save_task(self, instance):
        """Save the task and return to home screen"""
        message = self.task_input.text.strip()
        
        if not message:
            # Show error message (could be improved with a popup)
            self.task_input.hint_text = "Task message is required!"
            self.task_input.background_color = (1, 0.8, 0.8, 1)
            return
        
        # Create datetime from selected date and time
        task_datetime = datetime.combine(self.selected_date, self.selected_time)
        
        # Get task manager from home screen and add task
        home_screen = self.manager.get_screen("home")
        home_screen.task_manager.add_task(message=message, timestamp=task_datetime)
        
        # Reset form and go back to home
        self.reset_form()
        self.manager.current = "home"
    
    def reset_form(self):
        """Reset the form to default values"""
        self.task_input.text = ""
        self.task_input.hint_text = "Enter your task here"
        self.task_input.background_color = (1, 1, 1, 1)
        
        self.selected_date = datetime.now().date()
        self.selected_time = datetime.now().time()
        self.update_datetime_button()
    
    def on_enter(self):
        """Called when screen is entered"""
        # Reset the form
        self.reset_form()