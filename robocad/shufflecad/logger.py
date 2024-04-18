import logging
from datetime import datetime
from .shared import InfoHolder


class Logger:
    FORMAT = '[%(levelname)s]\t(%(threadName)-10s)\t%(message)s'

    def __init__(self):
        log_path = '/home/pi/robocad/logs/cad_main.log' if InfoHolder.on_real_robot else './cad_main.log'
        logging.basicConfig(level=logging.INFO,
                            format=self.FORMAT,
                            filename=log_path,
                            filemode='w+')
        self.main_logger = logging.getLogger()

    def write_main_log(self, s: str):
        self.main_logger.info(datetime.now().strftime("%H:%M:%S") + " " + s)
