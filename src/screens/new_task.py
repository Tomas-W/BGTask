from datetime import datetime
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from src.utils.buttons import TopBar, CustomButton
from src.utils.containers import BaseLayout, ScrollContainer, ButtonRow, Partition
from src.utils.fields import TextField, ButtonField

from src.settings import SCREEN


class NewTaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = TopBar(text="New Task", button=False)
        self.layout.add_widget(self.top_bar)
        
        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Date picker partition
        self.date_picker_partition = Partition()

        # Date picker button
        self.pick_date_button = CustomButton(text="Select Date", width=1, color_state="active")
        self.pick_date_button.bind(on_press=self.show_datetime_picker)
        self.date_picker_partition.add_widget(self.pick_date_button)
        
        # Date display box
        self.date_display = ButtonField(text="", width=1, color_state="inactive")
        self.date_picker_partition.add_widget(self.date_display)

        self.scroll_container.container.add_widget(self.date_picker_partition)

        # Task input partition
        self.task_input_partition = Partition()

        # Task input
        self.task_input = TextField(hint_text="Enter your task here")
        self.task_input_partition.add_widget(self.task_input)

        # Button row
        self.button_row = ButtonRow()
        # Cancel button
        self.cancel_button = CustomButton(text="Cancel", width=2, color_state="inactive")
        self.cancel_button.bind(on_press=self.cancel_task)
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = CustomButton(text="Save Task", width=2, color_state="active")
        self.save_button.bind(on_press=self.save_task)
        self.button_row.add_widget(self.save_button)
        self.task_input_partition.add_widget(self.button_row)
        self.scroll_container.container.add_widget(self.task_input_partition)

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
    
    def clear_inputs(self):
        """Clear the task input and date display data"""
        self.task_input.text = ""
        del self.selected_date
        del self.selected_time
        self.date_display.set_text("")

    def update_datetime_display(self):
        """Update the date display with the selected date and time"""
        if hasattr(self, 'selected_date') and hasattr(self, 'selected_time'):
            date_str = self.selected_date.strftime("%A, %B %d, %Y")
            time_str = self.selected_time.strftime("%H:%M")
            self.date_display.set_text(f"{date_str} at {time_str}")
            self.date_display.hide_border()
        else:
            self.date_display.set_text("")
    
    def show_datetime_picker(self, instance):
        """Show the calendar screen"""
        calendar_screen = self.manager.get_screen(SCREEN.CALENDAR)
        # Set the initial date and time if they exist
        if hasattr(self, 'selected_date'):
            calendar_screen.selected_date = self.selected_date
            calendar_screen.selected_time = self.selected_time
            calendar_screen.current_month = self.selected_date.month
            calendar_screen.current_year = self.selected_date.year
        # Set the callback
        calendar_screen.set_callback(self.on_datetime_selected)
        calendar_screen.update_calendar()  # Update the calendar display
        self.manager.current = SCREEN.CALENDAR

    def on_datetime_selected(self, selected_date, selected_time):
        """Callback when date and time are selected in calendar"""
        self.selected_date = selected_date
        self.selected_time = selected_time
        self.update_datetime_display()
        
        # Reset the date picker button styles
        self.date_display.hide_border()
    
    def cancel_task(self, instance):
        """Cancel task creation and return to home screen"""
        self.manager.current = SCREEN.HOME
    
    def save_task(self, instance):
        """Save the task and return to home screen"""
        message = self.task_input.text.strip()
        has_error = False
        
        # Visual error when no message
        if not message:
            self.task_input.show_error_border()
            has_error = True
        
        # Visual error when message too short
        if len(message.strip()) < 3:
            self.task_input.show_error_border()
            has_error = True
        
        # Visual error when no date selected
        if not hasattr(self, "selected_date") or not hasattr(self, "selected_time"):
            self.date_display.show_error_border()
            self.date_display.set_text("No date selected")
            has_error = True
        
        if has_error:
            return
        
        # Create and add task
        task_datetime = datetime.combine(self.selected_date, self.selected_time)
        home_screen = self.manager.get_screen(SCREEN.HOME)
        home_screen.task_manager.add_task(message=message, timestamp=task_datetime)
        self.clear_inputs()

        self.manager.current = SCREEN.HOME

    def on_pre_enter(self):
        """Called just before the screen is entered"""
        self.task_input.hide_border()
        self.date_display.hide_border()

    def on_enter(self):
        """Called when screen is entered"""
        self.date_display._set_inactive_state()
