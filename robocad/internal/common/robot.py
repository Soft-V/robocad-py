from abc import ABC
from datetime import datetime

import logging
from logging import Logger
from threading import Lock

from .robot_configuration import RobotConfiguration

class RobotInfo:
    def __init__(self):
        # some things
        self.spi_time_dev: float = 0
        self.rx_spi_time_dev: float = 0
        self.tx_spi_time_dev: float = 0
        self.spi_count_dev: float = 0
        self.com_time_dev: float = 0
        self.rx_com_time_dev: float = 0
        self.tx_com_time_dev: float = 0
        self.com_count_dev: float = 0
        self.temperature: float = 0
        self.memory_load: float = 0
        self.cpu_load: float = 0

class Robot(ABC):
    def __init__(self, on_real_robot, conf: RobotConfiguration):
        self.on_real_robot: bool = on_real_robot

        # logger object
        FORMAT = '[%(levelname)s]\t(%(threadName)-10s)\t%(message)s'
        log_path = conf.real_log_path if self.on_real_robot else conf.sim_log_path
        logging.basicConfig(level=logging.INFO,
                            format=FORMAT,
                            filename=log_path,
                            filemode='w+')
        self.logger: Logger = logging.getLogger()
        self.log_lock = Lock()

        # control the type of the shufflecad work
        self.power: float = 0.0

        # robot info
        self.robot_info: RobotInfo = RobotInfo()
    
    def write_log(self, s: str):
        with self.log_lock:
            self.logger.info(datetime.now().strftime("%H:%M:%S") + " " + s)