import time
import io
from abc import ABC

from .robot import Robot

class Updater(ABC):
    def __init__(self, robot: Robot):
        self.robot = robot
        self.stop_robot_info_thread = False

class RpiUpdater(Updater):
    def __init__(self, robot: Robot):
        super().__init__(robot)
    
    def updater(self):
        try:
            from gpiozero import CPUTemperature # type: ignore
            import psutil # type: ignore
            cpu_temp: CPUTemperature = CPUTemperature()
            while not self.stop_robot_info_thread:
                self.robot.robot_info.temperature = cpu_temp.temperature
                self.robot.robot_info.memory_load = psutil.virtual_memory().percent
                self.robot.robot_info.cpu_load = psutil.cpu_percent(interval=0.5)
                time.sleep(0.5)
        except Exception as e:
            self.robot.write_log(str(e))

class RepkaUpdater(Updater):
    def __init__(self, robot: Robot):
        super().__init__(robot)
    
    def updater(self):
        try:
            import psutil # type: ignore
            while not self.stop_robot_info_thread:
                with io.open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    self.robot.robot_info.temperature = float(f.read().strip()) / 1000
                self.robot.robot_info.memory_load = psutil.virtual_memory().percent
                self.robot.robot_info.cpu_load = psutil.cpu_percent(interval=0.5)
                time.sleep(0.5)
        except Exception as e:
            self.robot.write_log(str(e))