import os

from datetime import datetime, timedelta
from functools import lru_cache

from src.settings import DATE

def is_widget_visible(widget, scroll_view):
    if not widget or not scroll_view:
        return False
    
    # Get ScrollView viewport size and position
    view_y = scroll_view.y
    view_height = scroll_view.height
    view_bottom = view_y
    view_top = view_y + view_height
    
    # Get widget position relative to ScrollView
    widget_y = widget.to_window(*widget.pos)[1] - scroll_view.to_window(0, 0)[1]
    widget_height = widget.height
    widget_bottom = widget_y
    widget_top = widget_y + widget_height
    
    # Check if widget is fully visible in viewport
    return widget_bottom >= view_bottom and widget_top <= view_top


@lru_cache(maxsize=32)
def get_task_header_text(date_input) -> str:
    """
    Returns formatted date string with relative day names (Today, Tomorrow, etc.)
    
    Args:
        date_input: Can be either:
            - A datetime.date/datetime object
            - A string in format "Monday 24 Mar"
    
    Returns:
        Formatted string like "Today, January 1" or "Tomorrow, January 2"
    """
    today = datetime.now().date()
    
    # Convert input to date object []
    if isinstance(date_input, datetime):
        date = date_input.date()
    
    # Convert input to date object [21 Mar 2024]
    elif hasattr(date_input, 'day') and hasattr(date_input, 'month') and hasattr(date_input, 'year'):
        # This is a date object (has day, month, year attributes)
        date = date_input
    
    # Convert input to date object [21 Mar 2024]
    elif isinstance(date_input, str) and len(date_input.split()) >= 3:
        # Parse string in format "Monday 24 Mar"
        date_parts = date_input.split()
        day = int(date_parts[1])
        month = date_parts[2]
        current_year = datetime.now().year
        date = datetime.strptime(f"{day} {month} {current_year}", "%d %b %Y").date()
    
    else:
        # If we can't parse it, just return the input
        return str(date_input)
    
    # Format [Today March 21]
    month_day = date.strftime(DATE.MONTH_DAY)
    if date == today:
        return f"Today, {month_day}"
    
    elif date == today - timedelta(days=1):
        return f"Yesterday, {month_day}"
    
    elif date == today + timedelta(days=1):
        return f"Tomorrow, {month_day}"
    
    return date.strftime(DATE.TASK_HEADER)
