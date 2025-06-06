import functools

from src.utils.timer import TIMER
from src.utils.logger import logger


def log_time(name):
    """
    Decorator to log duration of a method or function.
    Usage: @log_time("name_to_time")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            TIMER.start(name)
            result = func(self, *args, **kwargs)
            TIMER.stop(name)
            
            logger.timing(f"Loading {name} took: {TIMER.get_time(name)}")
            return result
        return wrapper
    return decorator

