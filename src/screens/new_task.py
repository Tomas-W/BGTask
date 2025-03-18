from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from datetime import datetime

from src.utils.widgets import TopBar, ScrollContainer, ButtonActive, ButtonInactive, ButtonFieldActive, ButtonFieldInactive, Spacer
from src.screens.calendar import DateTimeButton, DateTimeLabel, DateTimePickerPopup
from src.settings import COL, SPACE, SIZE, STYLE, FONT


class NewTaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = FloatLayout()
        self.layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"top": 1, "center_x": 0.5}
        )
        
        # Top bar
        self.top_bar = TopBar(text="New Task", button=False)
        self.layout.add_widget(self.top_bar)
        
        # Scroll container
        self.scroll_container = ScrollContainer()

        spacer = Spacer(height=dp(SPACE.SPACE_Y_XL))
        self.scroll_container.container.add_widget(spacer)

        # Date picker button
        self.pick_date_button = ButtonActive(text="Pick Date", width=1)
        self.pick_date_button.bind(on_press=self.show_datetime_picker)
        self.scroll_container.container.add_widget(self.pick_date_button)  # Add to container
        
        # Date display box (initially empty)
        self.date_display = ButtonFieldInactive(width=1)
        # Label inside the date display box - centered text
        self.date_display_label = Label(
            text="",  # Initially empty
            color=COL.TEXT,
            font_size=dp(FONT.DEFAULT),
            halign="center",  # Centered text
            valign="middle",
            size_hint=(1, 1)
        )
        self.date_display_label.bind(size=self.date_display_label.setter("text_size"))
        self.date_display.add_widget(self.date_display_label)
        self.scroll_container.container.add_widget(self.date_display)

        # Task input
        self.task_input = TextInput(
            hint_text="Enter your task here",
            size_hint=(1, None),
            height=dp(SIZE.BUTTON_HEIGHT * 3),
            multiline=True,
            font_size=dp(FONT.DEFAULT),
            padding=[dp(SPACE.FIELD_PADDING_X), dp(SPACE.FIELD_PADDING_Y)]
        )
        self.scroll_container.container.add_widget(self.task_input)

        # Button row with cancel and save side by side
        self.button_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(SIZE.BUTTON_HEIGHT),
            spacing=dp(SPACE.SPACE_Y_M)
        )
        # Cancel button on the left
        self.cancel_button = ButtonInactive(text="Cancel", width=2)
        self.cancel_button.bind(on_press=self.cancel_task)
        self.button_row.add_widget(self.cancel_button)
        
        # Save button on the right
        self.save_button = ButtonActive(text="Save Task", width=2)
        self.save_button.bind(on_press=self.save_task)
        self.button_row.add_widget(self.save_button)

        self.scroll_container.container.add_widget(self.button_row)  # Add to container

        # Add scroll_container to layout
        self.layout.add_widget(self.scroll_container)
        
        # Add layout to root_layout - THIS WAS MISSING
        self.root_layout.add_widget(self.layout)
        
        # Add root_layout to screen
        self.add_widget(self.root_layout)
        
        # Initialize datetime
        self.selected_date = datetime.now().date()
        self.selected_time = datetime.now().time()
        self.update_datetime_display()
    
    
    
    def update_datetime_display(self):
        """Update the date display with the selected date and time"""
        if hasattr(self, 'selected_date') and hasattr(self, 'selected_time'):
            date_str = self.selected_date.strftime("%A, %B %d, %Y")
            time_str = self.selected_time.strftime("%H:%M")
            self.date_display_label.text = f"{date_str} at {time_str}"
        else:
            self.date_display_label.text = ""
    
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
        self.update_datetime_display()
    
    def cancel_task(self, instance):
        """Cancel task creation and return to home screen"""
        self.reset_form()
        self.manager.current = "home"
    
    def save_task(self, instance):
        """Save the task and return to home screen"""
        message = self.task_input.text.strip()
        
        if not message:
            # Show error message
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
        self.update_datetime_display()
    
    def on_enter(self):
        """Called when screen is entered"""
        # Reset the form
        self.reset_form()