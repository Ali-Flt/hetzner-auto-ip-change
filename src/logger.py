import os
from pathlib import Path
from datetime import datetime
import time
import logging

logging_logger = logging.getLogger(__name__)

class dataLogger:
    
    def __init__(self, pre_str : str = "", directory : str = "log", tz : str = None, logger=logging_logger) -> None:
        os.environ['TZ'] = tz
        time.tzset()
        self._directory = directory
        self._pre_str = pre_str
        self._logger = logger
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    def log(self, msg: str) -> None:
        if self._logger is not None:
            self._logger.warning(msg)
        with open(os.path.join(self._directory, f"{self._pre_str}{str(datetime.now().date())}.txt"), "a") as file:
            file.write(str(datetime.now().time()) + ":    " + msg + "\n")
