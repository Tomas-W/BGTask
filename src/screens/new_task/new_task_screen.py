from datetime import datetime
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from src.screens.base.base_screen import BaseScreen
from src.utils.buttons import CustomButton
from src.utils.containers import BaseLayout, ScrollContainer, Partition, CustomButtonRow
from src.utils.fields import TextField, ButtonField

from src.screens.new_task.new_task_utils import NewTaskBar, NewTaskBarExpanded

from src.settings import SCREEN, STATE


class NewTaskScreen(BaseScreen):
    def __init__(self, navigation_manager, task_manager, **kwargs):
        super().__init__(**kwargs)
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.edit_mode = False
        self.task_id_to_edit = None

        self.root_layout = FloatLayout()
        self.layout = BaseLayout()

        # Top bar
        self.top_bar = NewTaskBar(
            back_callback=lambda instance: self.navigation_manager.go_back(instance=instance),
            options_callback=self.switch_top_bar,
        )
        # Top bar with expanded options
        self.top_bar_expanded = NewTaskBarExpanded(
            back_callback=lambda instance: self.navigation_manager.go_back(instance=instance),
            options_callback=self.switch_top_bar,
            settings_callback=lambda instance: self.navigation_manager.go_to_settings_screen(instance=instance),
            exit_callback=lambda instance: self.navigation_manager.exit_app(instance=instance),
        )
        self.layout.add_widget(self.top_bar.top_bar_container)

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Date picker partition
        self.date_picker_partition = Partition()
        # Date picker button
        self.pick_date_button = CustomButton(text="Select Date", width=1, color_state=STATE.ACTIVE)
        self.pick_date_button.bind(on_press=self.go_to_select_date_screen)
        self.date_picker_partition.add_widget(self.pick_date_button)
        # Date display box
        self.date_display = ButtonField(text="", width=1, color_state=STATE.INACTIVE)
        self.date_picker_partition.add_widget(self.date_display)

        self.scroll_container.container.add_widget(self.date_picker_partition)

        # Task input partition
        self.task_input_partition = Partition()
        # Task input
        self.task_input = TextField(hint_text="Enter your task here")
        self.task_input_partition.add_widget(self.task_input)

        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomButton(text="Cancel", width=2, color_state=STATE.INACTIVE)
        self.cancel_button.bind(on_press=lambda instance: self.navigation_manager.go_back(instance=instance))
        self.button_row.add_widget(self.cancel_button)
        # Save button
        self.save_button = CustomButton(text="Save Task", width=2, color_state=STATE.ACTIVE)
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
        if hasattr(self, 'selected_date'):
            del self.selected_date
        if hasattr(self, 'selected_time'):
            del self.selected_time
        self.date_display.set_text("")
        self.edit_mode = False
        self.task_id_to_edit = None

    def update_datetime_display(self):
        """Update the date display with the selected date and time"""
        if hasattr(self, 'selected_date') and hasattr(self, 'selected_time'):
            date_str = self.selected_date.strftime("%A, %B %d, %Y")
            time_str = self.selected_time.strftime("%H:%M")
            self.date_display.set_text(f"{date_str} at {time_str}")
            self.date_display.hide_border()
        else:
            self.date_display.set_text("")

    def on_datetime_selected(self, selected_date, selected_time):
        """Callback when date and time are selected in calendar"""
        self.selected_date = selected_date
        self.selected_time = selected_time
        self.update_datetime_display()
        
        # Reset the date picker button styles
        self.date_display.hide_border()
    
    def cancel_task(self, instance):
        """Cancel task creation and return to home screen"""
        self.go_to_home_screen()
    
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
        
        # Create task datetime
        task_datetime = datetime.combine(self.selected_date, self.selected_time)
        
        if self.edit_mode:
            # Delete the old task
            self.task_manager.delete_task(self.task_id_to_edit)
            
            # Add the updated task
            self.task_manager.add_task(message=message, timestamp=task_datetime)
            
            # Reset edit mode
            self.edit_mode = False
            self.task_id_to_edit = None
        else:
            # Create and add new task
            self.task_manager.add_task(message=message, timestamp=task_datetime)
        
        self.clear_inputs()
        self.navigation_manager.go_back(instance=instance)

    def on_pre_enter(self):
        """Called just before the screen is entered"""
        super().on_pre_enter()
        self.task_input.hide_border()
        self.date_display.hide_border()
        
        # Update button text based on mode
        if self.edit_mode:
            self.save_button.text = "Update Task"
        else:
            self.save_button.text = "Save Task"

    def on_enter(self):
        """Called when screen is entered"""
        self.date_display._set_inactive_state()
    
    def go_to_select_date_screen(self, instance):
        """Show the calendar screen"""
        select_date_screen = self.manager.get_screen(SCREEN.SELECT_DATE)
        # Set the initial date and time if they exist
        if hasattr(self, 'selected_date'):
            select_date_screen.selected_date = self.selected_date
            select_date_screen.selected_time = self.selected_time
            select_date_screen.current_month = self.selected_date.month
            select_date_screen.current_year = self.selected_date.year
        # Set the callback
        select_date_screen.set_callback(self.on_datetime_selected)
        select_date_screen.update_calendar()
        self.navigation_manager.go_to_select_date_screen()
    