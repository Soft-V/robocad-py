from robocad.studica import RobotVmxTitan
import time


robot = RobotVmxTitan(False)

robot.motor_speed_0 = 30
robot.motor_speed_1 = -30
time.sleep(4)

robot.stop()
