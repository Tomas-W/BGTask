import calendar
from datetime import date, datetime

from kivy.graphics import Rectangle
from kivy.uix.label import Label


from .select_date_widgets import (DateTimeLabel, CalendarContainer,
                                  CalendarHeadersContainer, CalendarHeaderLabel,
                                  CalendarGrid)

from src.settings import SIZE


class SelectDateUtils:
    def __init__(self):
        pass
    
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
                    # Check if this day has any tasks
                    date_key = date(self.current_year, self.current_month, day).isoformat()
                    has_tasks = date_key in self.task_manager.tasks_by_date
                    
                    # Check if this is the current day
                    is_current_day = (day == datetime.now().day and 
                                    self.current_month == datetime.now().month and 
                                    self.current_year == datetime.now().year)
                    
                    # Check if this is the selected day
                    is_selected = (self.task_manager.selected_date and
                                 day == self.task_manager.selected_date.day and 
                                 self.current_month == self.task_manager.selected_date.month and 
                                 self.current_year == self.task_manager.selected_date.year)
                    
                    # Add underline markup if day has tasks
                    text = f"[u]{day}[/u]" if has_tasks else str(day)
                    day_button = DateTimeLabel(
                        text=text,
                        markup=True
                    )
                    
                    # Set current day highlight if applicable
                    if is_current_day:
                        day_button.set_current_day(True)
                    
                    # Set selected state if applicable
                    if is_selected:
                        day_button.set_selected(True)
                    
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
    
    def validate_hours(self, instance, value) -> None:
        """Allow any input during typing"""
        if len(value) > 2:
            instance.text = instance.text[:2]

    def validate_minutes(self, instance, value) -> None:
        """Allow any input during typing"""
        if len(value) > 2:
            instance.text = instance.text[:2]
