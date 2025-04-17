import calendar

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.label import Label


from .select_date_widgets import (DateTimeLabel, CalendarContainer,
                                  CalendarHeadersContainer, CalendarHeaderLabel,
                                  CalendarGrid)

from src.settings import COL, SIZE, STYLE


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
                    day_button = DateTimeLabel(
                        text=str(day),
                    )
                    
                    # Highlight the selected date if it exists
                    if (self.task_manager.selected_date and
                        day == self.task_manager.selected_date.day and 
                        self.current_month == self.task_manager.selected_date.month and 
                        self.current_year == self.task_manager.selected_date.year):
                        with day_button.canvas.before:
                            Color(*COL.FIELD_ACTIVE)
                            RoundedRectangle(pos=day_button.pos,
                                           size=day_button.size,
                                           radius=[STYLE.RADIUS_S])
                        day_button.color = COL.TEXT
                        day_button.set_bold(True)
                        day_button.bind(pos=self.update_selected_day, 
                                       size=self.update_selected_day)
                    
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
