import subprocess
from threading import Thread
import time
import cv2

from .connection_base import ConnectionBase
from .robot import Robot
from .shared import LibHolder
from .updaters import Updater
from .robot_configuration import RobotConfiguration
from .components.lidar import YDLidarX2


class ConnectionReal(ConnectionBase):
    def __init__(self, robot: Robot, updater: Updater, conf: RobotConfiguration):
        self.__robot = robot
        self.__updater = updater
        self.__lib = LibHolder(conf.lib_holder_first_path)

        try:
            self.__camera_instance = cv2.VideoCapture(conf.camera_index)
        except Exception as e:
            self.__robot.write_log("Exception while creating camera instance: ")
            self.__robot.write_log(str(e))

        try:
            self.__lidar_instance = YDLidarX2(conf.lidar_port, baudrate=115200, timeout=0.5)
        except Exception as e:
            self.__robot.write_log("Exception while creating lidar instance: ")
            self.__robot.write_log(str(e))

        # pi-blaster
        if conf.with_pi_blaster:
            subprocess.run(['sudo', '/home/pi/pi-blaster/pi-blaster'])
        # robot info thread
        self.__robot_info_thread: Thread = Thread(target=self.__updater.updater)
        self.__robot_info_thread.daemon = True
        self.__robot_info_thread.start()

    def stop(self) -> None:
        if self.__lidar_instance is not None:
            self.__lidar_instance.close()

        self.__updater.stop_robot_info_thread = True
        self.__robot_info_thread.join()

    def get_camera(self):
        try:
            ret, frame = self.__camera_instance.read()
            if ret:
                return frame
        except Exception:
            # there could be an error if there is no camera instance
            pass
        return None
    
    def get_lidar(self):
        try:
            return self.__lidar_instance.read_scan_packet(wait_timeout=1.0)
        except Exception:
            # there could be an error if there is no lidar instance
            pass
        return None
    
    def spi_ini(self, path: str, channel: int, speed: int, mode: int) -> int:
        return self.__lib.init_spi(path, channel, speed, mode)

    def com_ini(self, path: str, baud: int) -> int:
        return self.__lib.init_usb(path, baud)
    
    def spi_rw(self, array: bytearray) -> bytearray:
        return self.__lib.rw_spi(array)

    def com_rw(self, array: bytearray) -> bytearray:
        return self.__lib.rw_usb(array)
    
    def spi_stop(self):
        self.__lib.stop_spi()

    def com_stop(self):
        self.__lib.stop_usb()
