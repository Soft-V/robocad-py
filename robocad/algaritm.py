import signal
import threading

from .internal.common.robot import Robot
from .internal.common.robot_configuration import DefaultAlgaritmConfiguration
from .internal.algaritm_internal import AlgaritmInternal


class RobotAlgaritm(Robot):
    def __init__(self, is_real_robot: bool = True, conf: DefaultAlgaritmConfiguration = None):
        if conf is None: conf = DefaultAlgaritmConfiguration()

        super().__init__(is_real_robot, conf)
        self.__algaritm_internal = AlgaritmInternal(self, conf)
        self.__reseted_yaw_val = 0.0

        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self.handler)
            signal.signal(signal.SIGINT, self.handler)

    def stop(self):
        self.__algaritm_internal.stop()
        self.write_log("Program stopped")

    def handler(self, signum, _):
        self.write_log("Program stopped from handler")
        self.write_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    @property
    def motor_speed_0(self):
        return self.__algaritm_internal.speed_motor_0

    @motor_speed_0.setter
    def motor_speed_0(self, value):
        self.__algaritm_internal.speed_motor_0 = value

    @property
    def motor_speed_1(self):
        return self.__algaritm_internal.speed_motor_1

    @motor_speed_1.setter
    def motor_speed_1(self, value):
        self.__algaritm_internal.speed_motor_1 = value

    @property
    def motor_speed_2(self):
        return self.__algaritm_internal.speed_motor_2

    @motor_speed_2.setter
    def motor_speed_2(self, value):
        self.__algaritm_internal.speed_motor_2 = value

    @property
    def motor_speed_3(self):
        return self.__algaritm_internal.speed_motor_3

    @motor_speed_3.setter
    def motor_speed_3(self, value):
        self.__algaritm_internal.speed_motor_3 = value

    @property
    def motor_enc_0(self):
        return self.__algaritm_internal.enc_motor_0

    @property
    def motor_enc_1(self):
        return self.__algaritm_internal.enc_motor_1

    @property
    def motor_enc_2(self):
        return self.__algaritm_internal.enc_motor_2

    @property
    def motor_enc_3(self):
        return self.__algaritm_internal.enc_motor_3
    
    @property
    def yaw(self):
        return self.__algaritm_internal.yaw
    
    @property
    def pitch(self):
        return self.__algaritm_internal.pitch
    
    @property
    def roll(self):
        return self.__algaritm_internal.roll
    
    @property
    def us_1(self):
        return self.__algaritm_internal.ultrasound_1

    @property
    def us_2(self):
        return self.__algaritm_internal.ultrasound_2
    
    @property
    def us_3(self):
        return self.__algaritm_internal.ultrasound_3
    
    @property
    def us_4(self):
        return self.__algaritm_internal.ultrasound_4

    @property
    def analog_1(self):
        return self.__algaritm_internal.analog_1

    @property
    def analog_2(self):
        return self.__algaritm_internal.analog_2

    @property
    def analog_3(self):
        return self.__algaritm_internal.analog_3

    @property
    def analog_4(self):
        return self.__algaritm_internal.analog_4
    
    @property
    def analog_5(self):
        return self.__algaritm_internal.analog_5
    
    @property
    def analog_6(self):
        return self.__algaritm_internal.analog_6
    
    @property
    def analog_7(self):
        return self.__algaritm_internal.analog_7
    
    @property
    def analog_8(self):
        return self.__algaritm_internal.analog_8
    
    @property
    def additional_servo_1(self):
        return self.__algaritm_internal.additional_servo_1

    @additional_servo_1.setter
    def additional_servo_1(self, value):
        self.__algaritm_internal.additional_servo_1 = value

    @property
    def additional_servo_2(self):
        return self.__algaritm_internal.additional_servo_2

    @additional_servo_2.setter
    def additional_servo_2(self, value):
        self.__algaritm_internal.additional_servo_2 = value

    def set_pid_settings(self, use_pid, p, i, d):
        self.__algaritm_internal.use_pid = use_pid
        self.__algaritm_internal.p_pid = p
        self.__algaritm_internal.i_pid = i
        self.__algaritm_internal.d_pid = d

    # num 1 or 2
    def step_motor_move(self, num, steps: int, steps_per_second: int, direction: bool):
        self.__algaritm_internal.step_motor_move(num, steps, steps_per_second, direction)

    @property
    def is_step_1_busy(self):
        return self.__algaritm_internal.is_step_1_busy
    
    @property
    def is_step_2_busy(self):
        return self.__algaritm_internal.is_step_2_busy

    @property
    def titan_limits(self) -> list:
        return [self.__algaritm_internal.limit_h_0, self.__algaritm_internal.limit_l_0,
                self.__algaritm_internal.limit_h_1, self.__algaritm_internal.limit_l_1,
                self.__algaritm_internal.limit_h_2, self.__algaritm_internal.limit_l_2,
                self.__algaritm_internal.limit_h_3, self.__algaritm_internal.limit_l_3]

    @property
    def camera_image(self):
        return self.__algaritm_internal.get_camera()
    
    @property
    def lidar_data(self):
        return self.__algaritm_internal.get_lidar()
    
    # port is from 1 to 8 included
    def set_angle_servo(self, value: float, port: int):
        self.__algaritm_internal.set_servo_angle(value, port - 1)
