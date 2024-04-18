import time
import numpy as np
import cv2
import signal
from threading import Thread
import subprocess

from .shufflecad.shufflecad import Shufflecad
from .shufflecad.shared import InfoHolder
from .shufflecad.logger import Logger

from .robocadSim.studica.connection_helper import ConnectionHelper


class RobotVmxTitan:
    def __init__(self, is_real_robot: bool = True):
        self.__motor_speed_0 = 0.0
        self.__motor_speed_1 = 0.0
        self.__motor_speed_2 = 0.0
        self.__motor_speed_3 = 0.0

        self.__motor_enc_0 = 0.0
        self.__motor_enc_1 = 0.0
        self.__motor_enc_2 = 0.0
        self.__motor_enc_3 = 0.0

        self.__limit_l_0 = False
        self.__limit_h_0 = False
        self.__limit_l_1 = False
        self.__limit_h_1 = False
        self.__limit_l_2 = False
        self.__limit_h_2 = False
        self.__limit_l_3 = False
        self.__limit_h_3 = False

        self.__yaw = 0.0
        self.__reseted_yaw_val = 0.0

        self.__ultrasound_1 = 0.0
        self.__ultrasound_2 = 0.0

        self.__analog_1 = 0.0
        self.__analog_2 = 0.0
        self.__analog_3 = 0.0
        self.__analog_4 = 0.0

        self.__flex_0 = False
        self.__flex_1 = False
        self.__flex_2 = False
        self.__flex_3 = False
        self.__flex_4 = False
        self.__flex_5 = False
        self.__flex_6 = False
        self.__flex_7 = False

        self.__hcdio_values: list[float] = [0.0] * 10

        self.__camera_image = None

        self.is_real_robot = is_real_robot
        InfoHolder.on_real_robot = is_real_robot
        InfoHolder.logger = Logger()

        signal.signal(signal.SIGTERM, self.handler)
        signal.signal(signal.SIGINT, self.handler)

        if not self.is_real_robot:
            ConnectionHelper.start_channels()

            InfoHolder.power = "12"  # todo: control from sim
        else:
            try:
                self.__camera_instance = cv2.VideoCapture(0)
            except Exception as e:
                InfoHolder.logger.write_main_log("Exception while creating camera instance: ")
                InfoHolder.logger.write_main_log(str(e))
            # mb cringe
            global VMXStatic, TitanStatic, VMXSPI, TitanCOM
            from .pycad.studica.shared import VMXStatic, TitanStatic
            from .pycad.studica.SPI import VMXSPI
            from .pycad.studica.COM import TitanCOM
            VMXSPI.start_spi()
            TitanCOM.start_com()
            subprocess.run(['sudo', '/home/pi/pi-blaster/pi-blaster'])
            self.__stop_robot_info_thread = False
            self.__robot_info_thread: Thread = Thread(target=self.__update_rpi_cringe)
            self.__robot_info_thread.daemon = True
            self.__robot_info_thread.start()

    def __update_rpi_cringe(self):
        from gpiozero import CPUTemperature # type: ignore
        import psutil # type: ignore
        cpu_temp: CPUTemperature = CPUTemperature()
        while not self.__stop_robot_info_thread:
            InfoHolder.temperature = str(cpu_temp.temperature)
            InfoHolder.memory_load = str(psutil.virtual_memory().percent)
            InfoHolder.cpu_load = str(psutil.cpu_percent(interval=0.5))
            time.sleep(0.5)

    def stop(self):
        if not self.is_real_robot:
            ConnectionHelper.stop_channels()
        else:
            self.__stop_robot_info_thread = True
            self.__robot_info_thread.join()
            TitanCOM.stop_th = True
            TitanCOM.th.join()
            VMXSPI.stop_th = True
            VMXSPI.th.join()
        InfoHolder.logger.write_main_log("Program stopped")

    def handler(self, signum, _):
        InfoHolder.logger.write_main_log("Program stopped from handler")
        InfoHolder.logger.write_main_log('Signal handler called with signal' + str(signum))
        self.stop()
        raise SystemExit("Exited")

    @property
    def motor_speed_0(self):
        return self.__motor_speed_0

    @motor_speed_0.setter
    def motor_speed_0(self, value):
        self.__motor_speed_0 = value
        if not self.is_real_robot:
            self.__update_set_data()
        else:
            TitanStatic.speed_motor_0 = value

    @property
    def motor_speed_1(self):
        return self.__motor_speed_1

    @motor_speed_1.setter
    def motor_speed_1(self, value):
        self.__motor_speed_1 = value
        if not self.is_real_robot:
            self.__update_set_data()
        else:
            TitanStatic.speed_motor_1 = value

    @property
    def motor_speed_2(self):
        return self.__motor_speed_2

    @motor_speed_2.setter
    def motor_speed_2(self, value):
        self.__motor_speed_2 = value
        if not self.is_real_robot:
            self.__update_set_data()
        else:
            TitanStatic.speed_motor_2 = value

    @property
    def motor_speed_3(self):
        return self.__motor_speed_3

    @motor_speed_3.setter
    def motor_speed_3(self, value):
        self.__motor_speed_3 = value
        if not self.is_real_robot:
            self.__update_set_data()
        else:
            TitanStatic.speed_motor_3 = value

    @property
    def motor_enc_0(self):
        if not self.is_real_robot:
            self.__update_encs()
            return self.__motor_enc_0
        else:
            return TitanStatic.enc_motor_0

    @property
    def motor_enc_1(self):
        if not self.is_real_robot:
            self.__update_encs()
            return self.__motor_enc_1
        else:
            return TitanStatic.enc_motor_1

    @property
    def motor_enc_2(self):
        if not self.is_real_robot:
            self.__update_encs()
            return self.__motor_enc_2
        else:
            return TitanStatic.enc_motor_2

    @property
    def motor_enc_3(self):
        if not self.is_real_robot:
            self.__update_encs()
            return self.__motor_enc_3
        else:
            return TitanStatic.enc_motor_3

    @property
    def yaw(self):
        return self.__normalize_angle(self.__get_pure_yaw() - self.__reseted_yaw_val)
    
    def reset_yaw(self, value: float = 0.0):
        self.__reseted_yaw_val = self.__normalize_angle(self.__get_pure_yaw() - value)
        
    def __get_pure_yaw(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__yaw
        else:
            return VMXStatic.yaw

    @property
    def us_1(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__ultrasound_1
        else:
            return VMXStatic.ultrasound_1

    @property
    def us_2(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__ultrasound_2
        else:
            return VMXStatic.ultrasound_2

    @property
    def analog_1(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__analog_1
        else:
            return VMXStatic.analog_1

    @property
    def analog_2(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__analog_2
        else:
            return VMXStatic.analog_2

    @property
    def analog_3(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__analog_3
        else:
            return VMXStatic.analog_3

    @property
    def analog_4(self):
        if not self.is_real_robot:
            self.__update_sensors()
            return self.__analog_4
        else:
            return VMXStatic.analog_4

    @property
    def titan_limits(self) -> list:
        if not self.is_real_robot:
            self.__update_buttons()
            return [self.__limit_h_0, self.__limit_l_0,
                    self.__limit_h_1, self.__limit_l_1,
                    self.__limit_h_2, self.__limit_l_2,
                    self.__limit_h_3, self.__limit_l_3]
        else:
            return [TitanStatic.limit_h_0, TitanStatic.limit_l_0,
                    TitanStatic.limit_h_1, TitanStatic.limit_l_1,
                    TitanStatic.limit_h_2, TitanStatic.limit_l_2,
                    TitanStatic.limit_h_3, TitanStatic.limit_l_3]

    @property
    def vmx_flex(self) -> list:
        if not self.is_real_robot:
            self.__update_buttons()
            return [self.__flex_0, self.__flex_1,
                    self.__flex_2, self.__flex_3,
                    self.__flex_4, self.__flex_5,
                    self.__flex_6, self.__flex_7]
        else:
            return [VMXStatic.flex_0, VMXStatic.flex_1,
                    VMXStatic.flex_2, VMXStatic.flex_3,
                    VMXStatic.flex_4, VMXStatic.flex_5,
                    VMXStatic.flex_6, VMXStatic.flex_7]

    @property
    def camera_image(self):
        if not self.is_real_robot:
            self.__update_camera()
        else:
            try:
                ret, frame = self.__camera_instance.read()
                if ret:
                    self.__camera_image = frame
            except Exception:
                # there could be an error if there is no camera instance
                pass
        return self.__camera_image

    # port is from 1 to 10 included
    def set_angle_hcdio(self, value: float, port: int):
        if not self.is_real_robot:
            dut: float = 0.000666 * value + 0.05
            self.__hcdio_values[port - 1] = dut
            self.__update_set_data()
        else:
            VMXStatic.set_servo_angle(value, port - 1)

    # port is from 1 to 10 included
    def set_pwm_hcdio(self, value: float, port: int):
        if not self.is_real_robot:
            self.__hcdio_values[port - 1] = value
            self.__update_set_data()
        else:
            VMXStatic.set_servo_pwm(value, port - 1)

    # port is from 1 to 10 included
    def set_bool_hcdio(self, value: bool, port: int):
        if not self.is_real_robot:
            dut: float = 0.2 if value else 0.0
            self.__hcdio_values[port - 1] = dut
            self.__update_set_data()
        else:
            VMXStatic.set_led_state(value, port - 1)

    # for virtual robot
    def __update_set_data(self):
        values = [self.__motor_speed_0,
                  self.__motor_speed_1,
                  self.__motor_speed_2,
                  self.__motor_speed_3]
        values.extend(self.__hcdio_values)
        self.__connection_helper.set_data(tuple(values))

    def __update_encs(self):
        values = self.__connection_helper.get_data()
        if len(values) == ConnectionHelperVMXTitan.MAX_DATA_RECEIVE:
            self.__motor_enc_0 = values[0]
            self.__motor_enc_1 = values[1]
            self.__motor_enc_2 = values[2]
            self.__motor_enc_3 = values[3]

    def __update_sensors(self):
        values = self.__connection_helper.get_data()
        if len(values) == ConnectionHelperVMXTitan.MAX_DATA_RECEIVE:
            self.__ultrasound_1 = values[4]
            self.__ultrasound_2 = values[5]
            self.__analog_1 = values[6]
            self.__analog_2 = values[7]
            self.__analog_3 = values[8]
            self.__analog_4 = values[9]
            self.__yaw = values[10]

    def __update_buttons(self):
        values = self.__connection_helper.get_data()
        if len(values) == ConnectionHelperVMXTitan.MAX_DATA_RECEIVE:
            self.__limit_h_0 = values[11] == 1
            self.__limit_l_0 = values[12] == 1
            self.__limit_h_1 = values[13] == 1
            self.__limit_l_1 = values[14] == 1
            self.__limit_h_2 = values[15] == 1
            self.__limit_l_2 = values[16] == 1
            self.__limit_h_3 = values[17] == 1
            self.__limit_l_3 = values[18] == 1

            self.__flex_0 = values[19] == 1
            self.__flex_1 = values[20] == 1
            self.__flex_2 = values[21] == 1
            self.__flex_3 = values[22] == 1
            self.__flex_4 = values[23] == 1
            self.__flex_5 = values[24] == 1
            self.__flex_6 = values[25] == 1
            self.__flex_7 = values[26] == 1

    def __update_camera(self):
        # because of 640x480
        camera_data = ConnectionHelper.get_camera()
        if len(camera_data) == 921600:
            nparr = np.frombuffer(camera_data, np.uint8)
            if nparr.size > 0:
                img_rgb = nparr.reshape(480, 640, 3)
                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                self.__camera_image = img_bgr

    def __normalize_angle(self, angle: float) -> float:
        if angle < -180:
            return angle + 360
        elif angle > 180:
            return angle - 360
        return angle
