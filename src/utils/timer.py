import time

from src.utils.logger import logger


class Timer:
    def __init__(self):
        self.logs = {}
    
    def start(self, name: str):
        # if name in self.logs:
        #     raise ValueError(f"Timer {name} already started")
        
        self.logs[name] = [time.time(), None]
    
    def stop(self, name: str):
        if name not in self.logs:
            raise ValueError(f"Timer {name} not yet started")
        
        times = self.logs[name]
        times[1] = time.time()
        self.logs[name] = times
        logger.timing(self.get_time(name))
    
    def get_time(self, name: str):
        if name not in self.logs:
            raise ValueError(f"Timer {name} not found")
        
        if self.logs[name][0] is None:
            raise ValueError(f"Timer {name} not yet started")
        
        if self.logs[name][1] is None:
            raise ValueError(f"Timer {name} not yet stopped")
        
        times = self.logs[name]
        return f"Loading {name} took: {round(times[1] - times[0], 6)}"  # Only round the final difference
    
    def get_all_logs(self):
        logs = []
        for name, times in self.logs.items():
            try:
                logs.append(f"Loading {name} took: {round(times[1] - times[0], 6)}")
            except TypeError:
                print(f"Timer {name} failed, times: {times}")
        return logs


TIMER = Timer()
