import subprocess
from threading import Thread
import time
import cv2

from robocad.common import Common
from .connection_base import ConnectionBase

from .SPI import VMXSPI
from .COM import TitanCOM


class ConnectionReal(ConnectionBase):
    def start(self) -> None:
        try:
            self.__camera_instance = cv2.VideoCapture(0)
        except Exception as e:
            Common.logger.write_main_log("Exception while creating camera instance: ")
            Common.logger.write_main_log(str(e))

        VMXSPI.start_spi()
        TitanCOM.start_com()
        subprocess.run(['sudo', '/home/pi/pi-blaster/pi-blaster'])
        self.__stop_robot_info_thread = False
        self.__robot_info_thread: Thread = Thread(target=self.__update_rpi_cringe)
        self.__robot_info_thread.daemon = True
        self.__robot_info_thread.start()

    def stop(self) -> None:
        self.__stop_robot_info_thread = True
        self.__robot_info_thread.join()
        TitanCOM.stop_th = True
        TitanCOM.th.join()
        VMXSPI.stop_th = True
        VMXSPI.th.join()

    def get_camera(self):
        try:
            ret, frame = self.__camera_instance.read()
            if ret:
                return frame
        except Exception:
            # there could be an error if there is no camera instance
            pass
        return None
    
    def __update_rpi_cringe(self):
        from gpiozero import CPUTemperature # type: ignore
        import psutil # type: ignore
        cpu_temp: CPUTemperature = CPUTemperature()
        while not self.__stop_robot_info_thread:
            Common.temperature = cpu_temp.temperature
            Common.memory_load = psutil.virtual_memory().percent
            Common.cpu_load = psutil.cpu_percent(interval=0.5)
            time.sleep(0.5)
