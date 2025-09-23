import subprocess
from threading import Thread
import time
import cv2

from .connection_base import ConnectionBase
from .robot import Robot
from .shared import LibHolder


class ConnectionReal(ConnectionBase):
    def __init__(self, robot: Robot):
        self.__robot = robot
        self.__lib = LibHolder()

        try:
            self.__camera_instance = cv2.VideoCapture(0)
        except Exception as e:
            self.__robot.write_log("Exception while creating camera instance: ")
            self.__robot.write_log(str(e))

        # pi-blaster
        subprocess.run(['sudo', '/home/pi/pi-blaster/pi-blaster'])
        # robot info thread
        self.__stop_robot_info_thread = False
        self.__robot_info_thread: Thread = Thread(target=self.__update_rpi_cringe)
        self.__robot_info_thread.daemon = True
        self.__robot_info_thread.start()

    def stop(self) -> None:
        self.__stop_robot_info_thread = True
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
    
    def __update_rpi_cringe(self):
        from gpiozero import CPUTemperature # type: ignore
        import psutil # type: ignore
        cpu_temp: CPUTemperature = CPUTemperature()
        while not self.__stop_robot_info_thread:
            self.__robot.temperature = cpu_temp.temperature
            self.__robot.memory_load = psutil.virtual_memory().percent
            self.__robot.cpu_load = psutil.cpu_percent(interval=0.5)
            time.sleep(0.5)
