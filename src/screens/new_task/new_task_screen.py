from datetime import datetime

from src.screens.base.base_screen import BaseScreen

from src.widgets.buttons import CustomConfirmButton, CustomCancelButton
from src.widgets.containers import ScrollContainer, Partition, CustomButtonRow
from src.widgets.fields import TextField, ButtonField

from src.settings import SCREEN, STATE, TEXT


class NewTaskScreen(BaseScreen):
    """
    NewTaskScreen is the screen for creating or editing a new Task that:
    - Has a top bar with a back button, options button, and exit button.
    - Has a select date partition.
    - Has a task input partition.
    - Has a select alarm partition.
    - Has a confirmation partition.
    """
    MIN_TASK_LENGTH = 3
    
    def __init__(self, navigation_manager, task_manager, audio_manager, **kwargs):
        super().__init__(**kwargs)       
        self.navigation_manager = navigation_manager
        self.task_manager = task_manager
        self.audio_manager = audio_manager

        # Date and time attributes
        self.selected_date: datetime | None = None
        self.selected_time: datetime | None = None

        # Edit/delete attributes
        self.in_edit_task_mode: bool = False
        self.task_id_to_edit: int | None = None

        # TopBar title
        self.top_bar.bar_title.set_text("New Task")

        # Scroll container
        self.scroll_container = ScrollContainer(allow_scroll_y=False)

        # Date picker partition
        self.date_picker_partition = Partition()
        # Date picker button
        self.pick_date_button = CustomConfirmButton(text="Select Date", color_state=STATE.ACTIVE)
        self.pick_date_button.bind(on_release=self.go_to_select_date_screen)
        self.date_picker_partition.add_widget(self.pick_date_button)
        # Date display box
        self.date_display_field = ButtonField(text="", width=1, color_state=STATE.INACTIVE)
        self.date_picker_partition.add_widget(self.date_display_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.date_picker_partition)

        # Task input partition
        self.task_input_partition = Partition()
        # Task input
        self.task_input_field = TextField(hint_text="Enter your task here")
        self.task_input_partition.add_widget(self.task_input_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.task_input_partition)

        # Alarm picker partition
        self.select_alarm_partition = Partition()
        # Alarm picker button
        self.select_alarm_button = CustomConfirmButton(text="Select Alarm", color_state=STATE.ACTIVE)
        self.select_alarm_button.bind(on_release=lambda instance: self.navigation_manager.navigate_to(SCREEN.SELECT_ALARM))
        self.select_alarm_partition.add_widget(self.select_alarm_button)
        # Alarm display box
        self.alarm_display_field = ButtonField(text="", width=1, color_state=STATE.INACTIVE)
        self.select_alarm_partition.add_widget(self.alarm_display_field)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.select_alarm_partition)

        # Confirmation partition
        self.confirmation_partition = Partition()
        # Button row
        self.button_row = CustomButtonRow()
        # Cancel button
        self.cancel_button = CustomCancelButton(text="Cancel", width=2)
        self.cancel_button.bind(on_release=self.cancel_edit_task)
        self.button_row.add_widget(self.cancel_button)
        # Save button - with inactive state
        self.save_button = CustomConfirmButton(text="Save Task", width=2, color_state=STATE.INACTIVE)
        self.save_button.bind(on_release=self.save_task)
        self.button_row.add_widget(self.save_button)
        self.confirmation_partition.add_widget(self.button_row)
        # Add to Scroll container
        self.scroll_container.container.add_widget(self.confirmation_partition)

        # Add layouts
        self.layout.add_widget(self.scroll_container)
        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)
        
        # Set save_button state based on user inputs
        self.task_input_field.text_input.bind(text=self.validate_form)
    
    def cancel_edit_task(self, instance) -> None:
        """
        If in edit task mode, clear the inputs.
        Navigate back to the HomeScreen.
        """
        if self.in_edit_task_mode:
            self.clear_inputs()
        
        self.navigation_manager.navigate_back_to(SCREEN.HOME)
    
    def clear_inputs(self) -> None:
        """Clear the task_input_field and date_display_field data."""
        self.task_input_field.set_text("")
        self.selected_date = None
        self.selected_time = None
        self.date_display_field.set_text("")
        self.in_edit_task_mode = False
        self.task_id_to_edit = None
        self.audio_manager.selected_alarm_name = None
        self.audio_manager.selected_alarm_path = None
        self.save_button.set_inactive_state()
    
    def validate_form(self, *args) -> None:
        """
        Validates the Task input field and date/time selection.
        Updates the save_button state accordingly.
        """
        task_text = self.task_input_field.text.strip()
        date_time_set = self.selected_date is not None and self.selected_time is not None
        
        if len(task_text) >= 3 and date_time_set:
            self.save_button.set_active_state()
        else:
            self.save_button.set_inactive_state()

    def update_datetime_display(self) -> None:
        """
        Update the date_display_field with the selected date and time,
         or "No date selected".
        """
        if self.selected_date is not None and self.selected_time is not None:
            date_str = self.selected_date.strftime("%A, %B %d, %Y")
            time_str = self.selected_time.strftime("%H:%M")
            self.date_display_field.set_text(f"{date_str} at {time_str}")
            self.date_display_field.hide_border()
        else:
            self.date_display_field.set_text(TEXT.NO_DATE)

    def on_datetime_selected(self,
                             selected_date: datetime,
                             selected_time: datetime) -> None:
        """
        Callback when date and time are selected in the CalendarScreen.
        Set the selected_date and selected_time and update the date_display_field.
        """
        self.selected_date = selected_date
        self.selected_time = selected_time
        self.update_datetime_display()
        # Remove any visual errors
        self.date_display_field.hide_border()
        self.validate_form()
    
    def update_alarm_display(self) -> None:
        """
        Update the alarm_display_field with the selected alarm,
         or "No alarm set".
        """
        if self.audio_manager.selected_alarm_name is not None:
            self.alarm_display_field.set_text(self.audio_manager.selected_alarm_name)
        else:
            self.alarm_display_field.set_text(TEXT.NO_ALARM)
    
    def load_task_data(self, task) -> None:
        self.in_edit_task_mode = True
        self.edit_mode = True
        
        self.task_id_to_edit = task.task_id

        self.selected_date = task.timestamp.date()
        self.selected_time = task.timestamp.time()

        self.task_input_field.set_text(task.message)
        alarm_name = task.alarm_name if task.alarm_name else TEXT.NO_ALARM
        self.alarm_display_field.set_text(alarm_name)

        self.update_datetime_display()
    
    def save_task(self, instance) -> None:
        """
        Save the task and return to home screen.
        If the task_input_field is empty or too short, show an error border.
        If there is an error, return.
        Otherwise, save the task and clear the inputs.
        """
        message = self.task_input_field.text.strip()
        has_error = False
        
        # Visual error when no message
        if not message:
            self.task_input_field.show_error_border()
            has_error = True
        
        # Visual error when message too short
        if len(message.strip()) < self.MIN_TASK_LENGTH:
            self.task_input_field.show_error_border()
            has_error = True
        
        # Visual error when no date selected
        if self.selected_date is None or self.selected_time is None:
            self.date_display_field.show_error_border()
            has_error = True
        
        if has_error:
            return
        
        task_datetime = datetime.combine(self.selected_date, self.selected_time)
        if self.in_edit_task_mode:
            self.task_manager.update_task(
                task_id=self.task_id_to_edit,
                timestamp=task_datetime,
                message=message,
                alarm_name=self.audio_manager.selected_alarm_name
            )
            self.in_edit_task_mode = False
            self.task_id_to_edit = None
        else:
            self.task_manager.add_task(
                timestamp=task_datetime,
                message=message,
                alarm_name=self.audio_manager.selected_alarm_name
            )
        
        self.clear_inputs()
        self.navigation_manager.navigate_to(SCREEN.HOME)
    
    def go_to_select_date_screen(self, instance) -> None:
        select_date_screen = self.manager.get_screen(SCREEN.SELECT_DATE)
        
        # If in edit Task mode, load the task's datetime values
        if self.in_edit_task_mode and self.task_id_to_edit:
            select_date_screen.selected_date = self.selected_date
            select_date_screen.selected_time = self.selected_time
            select_date_screen.current_month = self.selected_date.month
            select_date_screen.current_year = self.selected_date.year
        else:
            # If new Task, use current values or else current datetime
            if self.selected_date:
                select_date_screen.selected_date = self.selected_date
                select_date_screen.selected_time = self.selected_time
                select_date_screen.current_month = self.selected_date.month
                select_date_screen.current_year = self.selected_date.year
        
        select_date_screen.set_callback(self.on_datetime_selected)
        select_date_screen.update_calendar()
        
        # Update time input fields
        if self.selected_time is not None:
            select_date_screen.hours_input.set_text(self.selected_time.strftime("%H"))
            select_date_screen.minutes_input.set_text(self.selected_time.strftime("%M"))
        
        # Update selected date label
        if self.selected_date is not None:
            date_str = self.selected_date.strftime("%A %d")
            select_date_screen.selected_date_label.set_text(f"{date_str}")
        
        self.navigation_manager.navigate_to(SCREEN.SELECT_DATE)

    def on_pre_enter(self) -> None:
        super().on_pre_enter()
        self.task_input_field.hide_border()
        self.date_display_field.hide_border()

        self.update_datetime_display()
        self.update_alarm_display()
        
        # Update button text based on mode
        if self.in_edit_task_mode:
            self.save_button.set_text("Update Task")
        else:
            self.save_button.set_text("Save Task")
        
        # Validate form state when entering screen
        self.validate_form()

    def on_enter(self) -> None:
        pass
