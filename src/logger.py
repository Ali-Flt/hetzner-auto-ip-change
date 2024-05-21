import os
from pathlib import Path
from datetime import datetime
import time

class dataLogger:
    
    def __init__(self, pre_str : str = "", directory : str = "log", tz : str = None) -> None:
        os.environ['TZ'] = tz
        time.tzset()
        self._directory = directory
        self._pre_str = pre_str
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    def log(self, msg: str) -> None:
        with open(os.path.join(self._directory, f"{self._pre_str}{str(datetime.now().date())}.txt"), "a") as file:
            file.write(str(datetime.now().time()) + ":    " + msg + "\n")
