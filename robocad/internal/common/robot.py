from abc import ABC
from datetime import datetime

import logging
from logging import Logger


class Robot(ABC):
    def __init__(self, on_real_robot = True):
        self.on_real_robot: bool = on_real_robot

        # logger object
        FORMAT = '[%(levelname)s]\t(%(threadName)-10s)\t%(message)s'
        log_path = '/home/pi/robocad/logs/main.log' if self.on_real_robot else './main.log'
        logging.basicConfig(level=logging.INFO,
                            format=FORMAT,
                            filename=log_path,
                            filemode='w+')
        self.logger: Logger = logging.getLogger()

        # control the type of the shufflecad work
        self.power: float = 0.0

        # some things
        self.__spi_time_dev: float = 0
        self.__rx_spi_time_dev: float = 0
        self.__tx_spi_time_dev: float = 0
        self.__spi_count_dev: float = 0
        self.__com_time_dev: float = 0
        self.__rx_com_time_dev: float = 0
        self.__tx_com_time_dev: float = 0
        self.__com_count_dev: float = 0
        self.__temperature: float = 0
        self.__memory_load: float = 0
        self.__cpu_load: float = 0
    
    def write_log(self, s: str):
        self.logger.info(datetime.now().strftime("%H:%M:%S") + " " + s)