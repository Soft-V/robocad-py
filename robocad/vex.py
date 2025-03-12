import signal

from .common import Common
from .internal.logger import Logger

from .internal.studica.connection_base import ConnectionBase
from .internal.studica.shared import VMXStatic, TitanStatic


class RobotVex:
    def __init__(self):
        self.__reseted_yaw_val = 0.0

        self.__connection: ConnectionBase = None

        Common.on_real_robot = False
        Common.logger = Logger()

        signal.signal(signal.SIGTERM, self.handler)
        signal.signal(signal.SIGINT, self.handler)

        from .internal.studica.connection_sim import ConnectionSim
        self.__connection = ConnectionSim()
        Common.power = 12  # todo: control from ConnectionSim from robocad

        self.__connection.start()

    def stop(self):
        self.__connection.stop()
        Common.logger.write_main_log("Program stopped")

    def handler(self, signum, _):
        Common.logger.write_main_log("Program stopped from handler")
        Common.logger.write_main_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    def get_motor_speed_right(self):
        return TitanStatic.speed_motor_0

    def set_motor_speed_right(self, value):
        TitanStatic.speed_motor_0 = value

    def get_motor_speed_left(self):
        return TitanStatic.speed_motor_1

    def set_motor_speed_left(self, value):
        TitanStatic.speed_motor_1 = value

    def get_motor_enc_right(self):
        return TitanStatic.enc_motor_0

    def get_motor_enc_left(self):
        return TitanStatic.enc_motor_1

    def get_gyro_degrees(self):
        return self.__normalize_angle(self.__get_pure_yaw() - self.__reseted_yaw_val)
    
    def reset_gyro_degrees(self, value: float = 0.0):
        self.__reseted_yaw_val = self.__normalize_angle(self.__get_pure_yaw() - value)
        
    def __get_pure_yaw(self):
        return VMXStatic.yaw
    
    def __normalize_angle(self, angle: float) -> float:
        if angle < -180:
            return angle + 360
        elif angle > 180:
            return angle - 360
        return angle

    def set_servo_claw(self, value):
        VMXStatic.set_servo_angle(value, 3)

    def set_servo_arm(self, value):
        VMXStatic.set_servo_angle(value, 4)
