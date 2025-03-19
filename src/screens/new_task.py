from datetime import datetime
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from src.screens.calendar import DateTimePickerPopup
from src.utils.buttons import TopBar, CustomButton
from src.utils.containers import BaseLayout, ScrollContainer, ButtonRow
from src.utils.fields import TextField, ButtonField
from src.utils.misc import Spacer

from src.settings import SCREEN, SPACE


class NewTaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = TopBar(text="New Task", button=False)
        self.layout.add_widget(self.top_bar)
        
        # Scroll container
        self.scroll_container = ScrollContainer()

        # Spacer
        spacer = Spacer(height=dp(SPACE.SPACE_Y_XL))
        self.scroll_container.container.add_widget(spacer)

        # Date picker button
        self.pick_date_button = CustomButton(text="Select Date", width=1, color_state="active")
        self.pick_date_button.bind(on_press=self.show_datetime_picker)
        self.scroll_container.container.add_widget(self.pick_date_button)
        
        # Date display box
        self.date_display = ButtonField(text="", width=1, color_state="inactive")
        # self.date_display_label = ButtonFieldLabel(text="")
        # self.date_display.add_widget(self.date_display_label)
        self.scroll_container.container.add_widget(self.date_display)

        # Task input with styled background
        self.task_input = TextField(hint_text="Enter your task here")
        self.scroll_container.container.add_widget(self.task_input)

        # Button row
        self.button_row = ButtonRow()
        # Cancel button on the left
        self.cancel_button = CustomButton(text="Cancel", width=2, color_state="inactive")
        self.cancel_button.bind(on_press=self.cancel_task)
        self.button_row.add_widget(self.cancel_button)
        # Save button on the right
        self.save_button = CustomButton(text="Save Task", width=2, color_state="active")
        self.save_button.bind(on_press=self.save_task)
        self.button_row.add_widget(self.save_button)

        self.scroll_container.container.add_widget(self.button_row)

        # Add scroll_container to layout
        self.layout.add_widget(self.scroll_container)
        
        # Add layout to root_layout
        self.root_layout.add_widget(self.layout)
        
        # Add root_layout to screen
        self.add_widget(self.root_layout)
    
    def clear_inputs(self):
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
        """Show the datetime picker popup"""
        popup = DateTimePickerPopup(
            selected_date=self.selected_date if hasattr(self, 'selected_date') else datetime.now().date(),
            selected_time=self.selected_time if hasattr(self, 'selected_time') else datetime.now().time(),
            callback=self.on_datetime_selected
        )
        popup.open()
    
    def on_datetime_selected(self, selected_date, selected_time):
        """Callback when date and time are selected in the popup"""
        self.selected_date = selected_date
        self.selected_time = selected_time
        self.update_datetime_display()
        
        # Reset the date picker button to normal state
        self.date_display.hide_border()
    
    def cancel_task(self, instance):
        """Cancel task creation and return to home screen"""
        self.manager.current = SCREEN.HOME
    
    def save_task(self, instance):
        """Save the task and return to home screen"""
        message = self.task_input.text.strip()
        has_error = False
        
        # Validate task message
        if not message:
            self.task_input.show_error_border()
            has_error = True
        
        if len(message.strip()) < 3:
            self.task_input.show_error_border()
            has_error = True
        
        # Validate date selection
        if not hasattr(self, "selected_date") or not hasattr(self, "selected_time"):
            # Set button to error state
            self.date_display.show_error_border()
            self.date_display.set_text("No date selected")
            has_error = True
        
        if has_error:
            return
        
        # Create datetime from selected date and time
        task_datetime = datetime.combine(self.selected_date, self.selected_time)
        
        # Get task manager from home screen and add task
        home_screen = self.manager.get_screen(SCREEN.HOME)
        home_screen.task_manager.add_task(message=message, timestamp=task_datetime)
        self.clear_inputs()

        self.manager.current = SCREEN.HOME

    def on_pre_enter(self):
        """Called just before the screen is entered"""
        self.task_input.hide_border()  # Reset the input border
        self.date_display.hide_border()  # Reset the date display border

    def on_enter(self):
        """Called when screen is entered"""
        self.date_display._set_inactive_state()  # Set date display to inactive state
