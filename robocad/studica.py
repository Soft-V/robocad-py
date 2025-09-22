import signal

from .internal.common.robot import Robot
from .internal.studica_internal import StudicaInternal


class RobotVmxTitan(Robot):
    def __init__(self, is_real_robot: bool = True):
        super().__init__(is_real_robot)
        self.__studica_internal = StudicaInternal(self)
        self.__reseted_yaw_val = 0.0

        signal.signal(signal.SIGTERM, self.handler)
        signal.signal(signal.SIGINT, self.handler)

    def stop(self):
        self.__studica_internal.stop()
        self.write_log("Program stopped")

    def handler(self, signum, _):
        self.write_log("Program stopped from handler")
        self.write_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    @property
    def motor_speed_0(self):
        return self.__studica_internal.speed_motor_0

    @motor_speed_0.setter
    def motor_speed_0(self, value):
        self.__studica_internal.speed_motor_0 = value

    @property
    def motor_speed_1(self):
        return self.__studica_internal.speed_motor_1

    @motor_speed_1.setter
    def motor_speed_1(self, value):
        self.__studica_internal.speed_motor_1 = value

    @property
    def motor_speed_2(self):
        return self.__studica_internal.speed_motor_2

    @motor_speed_2.setter
    def motor_speed_2(self, value):
        self.__studica_internal.speed_motor_2 = value

    @property
    def motor_speed_3(self):
        return self.__studica_internal.speed_motor_3

    @motor_speed_3.setter
    def motor_speed_3(self, value):
        self.__studica_internal.speed_motor_3 = value

    @property
    def motor_enc_0(self):
        return self.__studica_internal.enc_motor_0

    @property
    def motor_enc_1(self):
        return self.__studica_internal.enc_motor_1

    @property
    def motor_enc_2(self):
        return self.__studica_internal.enc_motor_2

    @property
    def motor_enc_3(self):
        return self.__studica_internal.enc_motor_3
    
    @property
    def yaw(self):
        return self.__studica_internal.yaw_unlim

    @property
    def yaw(self):
        return self.__normalize_angle(self.__get_pure_yaw() - self.__reseted_yaw_val)
    
    def reset_yaw(self, value: float = 0.0):
        self.__reseted_yaw_val = self.__normalize_angle(self.__get_pure_yaw() - value)
        
    def __get_pure_yaw(self):
        return self.__studica_internal.yaw
    
    def __normalize_angle(self, angle: float) -> float:
        if angle < -180:
            return angle + 360
        elif angle > 180:
            return angle - 360
        return angle

    @property
    def us_1(self):
        return self.__studica_internal.ultrasound_1

    @property
    def us_2(self):
        return self.__studica_internal.ultrasound_2

    @property
    def analog_1(self):
        return self.__studica_internal.analog_1

    @property
    def analog_2(self):
        return self.__studica_internal.analog_2

    @property
    def analog_3(self):
        return self.__studica_internal.analog_3

    @property
    def analog_4(self):
        return self.__studica_internal.analog_4

    @property
    def titan_limits(self) -> list:
        return [self.__studica_internal.limit_h_0, self.__studica_internal.limit_l_0,
                self.__studica_internal.limit_h_1, self.__studica_internal.limit_l_1,
                self.__studica_internal.limit_h_2, self.__studica_internal.limit_l_2,
                self.__studica_internal.limit_h_3, self.__studica_internal.limit_l_3]

    @property
    def vmx_flex(self) -> list:
        return [self.__studica_internal.flex_0, self.__studica_internal.flex_1,
                self.__studica_internal.flex_2, self.__studica_internal.flex_3,
                self.__studica_internal.flex_4, self.__studica_internal.flex_5,
                self.__studica_internal.flex_6, self.__studica_internal.flex_7]

    @property
    def camera_image(self):
        return self.__studica_internal.get_camera()

    # port is from 1 to 10 included
    def set_angle_hcdio(self, value: float, port: int):
        self.__studica_internal.set_servo_angle(value, port - 1)

    # port is from 1 to 10 included
    def set_pwm_hcdio(self, value: float, port: int):
        self.__studica_internal.set_servo_pwm(value, port - 1)

    # port is from 1 to 10 included
    def set_bool_hcdio(self, value: bool, port: int):
        self.__studica_internal.set_led_state(value, port - 1)
