import signal

from .internal.common.robot import Robot
from .internal.algaritm_internal import AlgaritmInternal


class RobotAlgaritm(Robot):
    def __init__(self, is_real_robot: bool = True):
        super().__init__(is_real_robot)
        self.__algaritm_internal = AlgaritmInternal(self)
        self.__reseted_yaw_val = 0.0

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
    def titan_limits(self) -> list:
        return [self.__algaritm_internal.limit_h_0, self.__algaritm_internal.limit_l_0,
                self.__algaritm_internal.limit_h_1, self.__algaritm_internal.limit_l_1,
                self.__algaritm_internal.limit_h_2, self.__algaritm_internal.limit_l_2,
                self.__algaritm_internal.limit_h_3, self.__algaritm_internal.limit_l_3]

    @property
    def camera_image(self):
        return self.__algaritm_internal.get_camera()
