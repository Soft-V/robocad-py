import signal

from .common import Common
from .internal.logger import Logger

from .internal.studica.connection_base import ConnectionBase
from .internal.studica.shared import VMXStatic, TitanStatic


class RobotVmxTitan:
    def __init__(self, is_real_robot: bool = True):
        self.__reseted_yaw_val = 0.0

        self.__connection: ConnectionBase = None

        Common.on_real_robot = is_real_robot
        Common.logger = Logger()

        signal.signal(signal.SIGTERM, self.handler)
        signal.signal(signal.SIGINT, self.handler)

        if not is_real_robot:
            from .internal.studica.connection_sim import ConnectionSim
            self.__connection = ConnectionSim()
            Common.power = 12  # todo: control from ConnectionSim from robocad
        else:
            from .internal.studica.connection_real import ConnectionReal
            self.__connection = ConnectionReal()
        self.__connection.start()

    def stop(self):
        self.__connection.stop()
        Common.logger.write_main_log("Program stopped")

    def handler(self, signum, _):
        Common.logger.write_main_log("Program stopped from handler")
        Common.logger.write_main_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    @property
    def motor_speed_0(self):
        return TitanStatic.speed_motor_0

    @motor_speed_0.setter
    def motor_speed_0(self, value):
        TitanStatic.speed_motor_0 = value

    @property
    def motor_speed_1(self):
        return TitanStatic.speed_motor_1

    @motor_speed_1.setter
    def motor_speed_1(self, value):
        TitanStatic.speed_motor_1 = value

    @property
    def motor_speed_2(self):
        return TitanStatic.speed_motor_2

    @motor_speed_2.setter
    def motor_speed_2(self, value):
        TitanStatic.speed_motor_2 = value

    @property
    def motor_speed_3(self):
        return TitanStatic.speed_motor_3

    @motor_speed_3.setter
    def motor_speed_3(self, value):
        TitanStatic.speed_motor_3 = value

    @property
    def motor_enc_0(self):
        return TitanStatic.enc_motor_0

    @property
    def motor_enc_1(self):
        return TitanStatic.enc_motor_1

    @property
    def motor_enc_2(self):
        return TitanStatic.enc_motor_2

    @property
    def motor_enc_3(self):
        return TitanStatic.enc_motor_3

    @property
    def yaw(self):
        return self.__normalize_angle(self.__get_pure_yaw() - self.__reseted_yaw_val)
    
    def reset_yaw(self, value: float = 0.0):
        self.__reseted_yaw_val = self.__normalize_angle(self.__get_pure_yaw() - value)
        
    def __get_pure_yaw(self):
        return VMXStatic.yaw
    
    def __normalize_angle(self, angle: float) -> float:
        if angle < -180:
            return angle + 360
        elif angle > 180:
            return angle - 360
        return angle

    @property
    def us_1(self):
        return VMXStatic.ultrasound_1

    @property
    def us_2(self):
        return VMXStatic.ultrasound_2

    @property
    def analog_1(self):
        return VMXStatic.analog_1

    @property
    def analog_2(self):
        return VMXStatic.analog_2

    @property
    def analog_3(self):
        return VMXStatic.analog_3

    @property
    def analog_4(self):
        return VMXStatic.analog_4

    @property
    def titan_limits(self) -> list:
        return [TitanStatic.limit_h_0, TitanStatic.limit_l_0,
                TitanStatic.limit_h_1, TitanStatic.limit_l_1,
                TitanStatic.limit_h_2, TitanStatic.limit_l_2,
                TitanStatic.limit_h_3, TitanStatic.limit_l_3]

    @property
    def vmx_flex(self) -> list:
        return [VMXStatic.flex_0, VMXStatic.flex_1,
                VMXStatic.flex_2, VMXStatic.flex_3,
                VMXStatic.flex_4, VMXStatic.flex_5,
                VMXStatic.flex_6, VMXStatic.flex_7]

    @property
    def camera_image(self):
        return self.__connection.get_camera()

    # port is from 1 to 10 included
    def set_angle_hcdio(self, value: float, port: int):
        VMXStatic.set_servo_angle(value, port - 1)

    # port is from 1 to 10 included
    def set_pwm_hcdio(self, value: float, port: int):
        VMXStatic.set_servo_pwm(value, port - 1)

    # port is from 1 to 10 included
    def set_bool_hcdio(self, value: bool, port: int):
        VMXStatic.set_led_state(value, port - 1)
