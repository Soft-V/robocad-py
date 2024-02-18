import logging
from datetime import datetime
from .shared import InfoHolder


class Logger:
    FORMAT = '[%(levelname)s] (%(threadName)-10s) %(message)s'

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG,
                            format=self.FORMAT)
        if InfoHolder.on_real_robot:
            file_handler = logging.FileHandler('/home/pi/robocad/logs/cad_main.log')
        else:
            file_handler = logging.FileHandler('./cad_main.log')
        file_handler.setFormatter(logging.Formatter(self.FORMAT))
        self.main_logger = logging.getLogger("main_logger")
        self.main_logger.addHandler(file_handler)
        self.main_logger.setLevel(logging.WARNING)

    def write_main_log(self, s: str):
        self.main_logger.info(datetime.now().strftime("%H:%M:%S") + " " + s)
