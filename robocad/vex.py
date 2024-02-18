import signal

from .shufflecad.shufflecad import Shufflecad
from .shufflecad.shared import InfoHolder

from .robocadSim.connection_helper_vmx_titan import ConnectionHelperVMXTitan


class RobocadVex:
    def __init__(self):
        self.__motor_speed_right = 0.0
        self.__motor_speed_left = 0.0

        self.__motor_enc_right = 0.0
        self.__motor_enc_left = 0.0

        self.__yaw = 0.0

        self.__hcdio_values: list = [0] * 10

        self.is_real_robot = False
        InfoHolder.on_real_robot = False
        Shufflecad.start()

        signal.signal(signal.SIGTERM, self.handler)
        signal.signal(signal.SIGINT, self.handler)
        self.__connection_helper = ConnectionHelperVMXTitan()
        self.__connection_helper.start_channels()

        InfoHolder.power = "12"  # :)

    def stop(self):
        Shufflecad.stop()
        self.__connection_helper.stop_channels()
        InfoHolder.logger.write_main_log("Program stopped")

    def handler(self, signum, _):
        InfoHolder.logger.write_main_log("Program stopped from handler")
        InfoHolder.logger.write_main_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    def set_servo_claw(self, value):
        self.__set_angle_hcdio(value, 1)

    def set_servo_arm(self, value):
        self.__set_angle_hcdio(value, 2)

    def set_motor_speed_right(self, value):
        self.__motor_speed_right = value
        self.__update_set_data()

    def set_motor_speed_left(self, value):
        self.__motor_speed_left = value
        self.__update_set_data()

    def get_motor_encoder_right(self):
        self.__update_encs()
        return self.__motor_enc_right

    def get_motor_encoder_left(self):
        self.__update_encs()
        return self.__motor_enc_left

    def get_gyro_degrees(self):
        self.__update_sensors()
        return self.__yaw

    # port is from 1 to 10 included
    def __set_angle_hcdio(self, value: float, port: int):
        dut: float = 0.000666 * value + 0.05
        self.__hcdio_values[port - 1] = dut
        self.__update_set_data()

    # for virtual robot
    def __update_set_data(self):
        values = [self.__motor_speed_right,
                  self.__motor_speed_left,
                  0,
                  0]
        values.extend(self.__hcdio_values)
        self.__connection_helper.set_data(tuple(values))

    def __update_encs(self):
        values = self.__connection_helper.get_data()
        if len(values) == ConnectionHelperVMXTitan.MAX_DATA_RECEIVE:
            self.__motor_enc_right = values[0]
            self.__motor_enc_left = values[1]

    def __update_sensors(self):
        values = self.__connection_helper.get_data()
        if len(values) == ConnectionHelperVMXTitan.MAX_DATA_RECEIVE:
            self.__yaw = values[10]
