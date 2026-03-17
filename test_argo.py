from robocad.common import CommonRobot
from robocad.shufflecad import Shufflecad, ShuffleVariable, CameraVariable
import time


robot = CommonRobot(False)
shufflecad = Shufflecad(robot)

ir1: ShuffleVariable = shufflecad.add_var(ShuffleVariable("ir1", ShuffleVariable.FLOAT_TYPE, ShuffleVariable.OUT_VAR))
ir2: ShuffleVariable = shufflecad.add_var(ShuffleVariable("ir2", ShuffleVariable.FLOAT_TYPE, ShuffleVariable.OUT_VAR))
us1: ShuffleVariable = shufflecad.add_var(ShuffleVariable("us1", ShuffleVariable.FLOAT_TYPE, ShuffleVariable.OUT_VAR))
us2: ShuffleVariable = shufflecad.add_var(ShuffleVariable("us2", ShuffleVariable.FLOAT_TYPE, ShuffleVariable.OUT_VAR))
yaw1: ShuffleVariable = shufflecad.add_var(ShuffleVariable("yaw", ShuffleVariable.FLOAT_TYPE, ShuffleVariable.OUT_VAR))
cam: CameraVariable = shufflecad.add_var(CameraVariable("c1"))

st_time = time.time()
while time.time() - st_time < 30:
    # скорости от -100 до 100
    robot.motor_speed_0 = 70 
    robot.motor_speed_1 = 70

    ir1.set_float(robot.analog_1)
    ir2.set_float(robot.analog_2)
    us1.set_float(robot.us_1)
    us2.set_float(robot.us_2)
    yaw1.set_float(robot.yaw)

    if robot.camera_image is not None:
        cam.set_mat(robot.camera_image)

    time.sleep(0.5)

shufflecad.stop()
robot.stop()

