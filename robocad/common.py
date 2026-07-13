import signal
import threading
import cv2

from .internal.common.robot import Robot
from .internal.common.robot_configuration import DefaultCommonConfiguration
from .internal.common_internal import CommonRobotInternal


class CommonRobot(Robot):
    def __init__(self, is_real_robot: bool = True, conf: DefaultCommonConfiguration = None):
        if conf is None: conf = DefaultCommonConfiguration()

        super().__init__(is_real_robot, conf)
        self.__common_internal = CommonRobotInternal(self, conf)

        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self.handler)
            signal.signal(signal.SIGINT, self.handler)

    def stop(self):
        self.__common_internal.stop()
        self.write_log("Program stopped")

    def handler(self, signum, _):
        self.write_log("Program stopped from handler")
        self.write_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    @property
    def motor_speed_0(self):
        return self.__common_internal.speed_motor_0

    @motor_speed_0.setter
    def motor_speed_0(self, value):
        self.__common_internal.speed_motor_0 = value

    @property
    def motor_speed_1(self):
        return self.__common_internal.speed_motor_1

    @motor_speed_1.setter
    def motor_speed_1(self, value):
        self.__common_internal.speed_motor_1 = value

    @property
    def motor_speed_2(self):
        return self.__common_internal.speed_motor_2

    @motor_speed_2.setter
    def motor_speed_2(self, value):
        self.__common_internal.speed_motor_2 = value

    @property
    def motor_speed_3(self):
        return self.__common_internal.speed_motor_3

    @motor_speed_3.setter
    def motor_speed_3(self, value):
        self.__common_internal.speed_motor_3 = value

    @property
    def motor_speed_4(self):
        return self.__common_internal.speed_motor_4

    @motor_speed_4.setter
    def motor_speed_4(self, value):
        self.__common_internal.speed_motor_4 = value

    @property
    def motor_speed_5(self):
        return self.__common_internal.speed_motor_5

    @motor_speed_5.setter
    def motor_speed_5(self, value):
        self.__common_internal.speed_motor_5 = value

    @property
    def motor_speed_6(self):
        return self.__common_internal.speed_motor_6

    @motor_speed_6.setter
    def motor_speed_6(self, value):
        self.__common_internal.speed_motor_6 = value

    @property
    def motor_speed_7(self):
        return self.__common_internal.speed_motor_7

    @motor_speed_7.setter
    def motor_speed_7(self, value):
        self.__common_internal.speed_motor_7 = value

    @property
    def motor_enc_0(self):
        return self.__common_internal.enc_motor_0

    @property
    def motor_enc_1(self):
        return self.__common_internal.enc_motor_1

    @property
    def motor_enc_2(self):
        return self.__common_internal.enc_motor_2

    @property
    def motor_enc_3(self):
        return self.__common_internal.enc_motor_3
    
    @property
    def motor_enc_4(self):
        return self.__common_internal.enc_motor_4
    
    @property
    def motor_enc_5(self):
        return self.__common_internal.enc_motor_5
    
    @property
    def motor_enc_6(self):
        return self.__common_internal.enc_motor_6
    
    @property
    def motor_enc_7(self):
        return self.__common_internal.enc_motor_7
    
    @property
    def yaw(self):
        return self.__common_internal.yaw

    @property
    def us_1(self):
        return self.__common_internal.ultrasound_1

    @property
    def us_2(self):
        return self.__common_internal.ultrasound_2
    
    @property
    def us_3(self):
        return self.__common_internal.ultrasound_3
    
    @property
    def us_4(self):
        return self.__common_internal.ultrasound_4

    @property
    def analog_1(self):
        return self.__common_internal.analog_1

    @property
    def analog_2(self):
        return self.__common_internal.analog_2

    @property
    def analog_3(self):
        return self.__common_internal.analog_3

    @property
    def analog_4(self):
        return self.__common_internal.analog_4
    
    @property
    def analog_5(self):
        return self.__common_internal.analog_5
    
    @property
    def analog_6(self):
        return self.__common_internal.analog_6
    
    @property
    def analog_7(self):
        return self.__common_internal.analog_7
    
    @property
    def analog_8(self):
        return self.__common_internal.analog_8

    @property
    def buttons(self) -> list:
        return [self.__common_internal.button_0, self.__common_internal.button_1,
                self.__common_internal.button_2, self.__common_internal.button_3,
                self.__common_internal.button_4, self.__common_internal.button_5,
                self.__common_internal.button_6, self.__common_internal.button_7]
    
    @property
    def led_0(self):
        return self.__common_internal.led_0
    @led_0.setter
    def led_0(self, value):
        self.__common_internal.led_0 = value

    @property
    def led_1(self):
        return self.__common_internal.led_1
    @led_1.setter
    def led_1(self, value):
        self.__common_internal.led_1 = value

    @property
    def led_2(self):
        return self.__common_internal.led_2
    @led_2.setter
    def led_2(self, value):
        self.__common_internal.led_2 = value

    @property
    def led_3(self):
        return self.__common_internal.led_3
    @led_3.setter
    def led_3(self, value):
        self.__common_internal.led_3 = value

    @property
    def camera_image(self):
        return self.__common_internal.get_camera()

    # port is from 1 to 10 included
    def set_angle_servo(self, value: float, port: int):
        self.__common_internal.set_servo_angle(value, port - 1)

    # port is from 1 to 10 included
    def set_pwm_servo(self, value: float, port: int):
        self.__common_internal.set_servo_pwm(value, port - 1)
