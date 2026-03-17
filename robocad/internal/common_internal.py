import struct
import time
from threading import Thread

from .common.robot import Robot
from .common.connection_base import ConnectionBase
from .common.connection_sim import ConnectionSim
from .common.robot_configuration import DefaultCommonConfiguration


class CommonRobotInternal:
    def __init__(self, robot: Robot, conf: DefaultCommonConfiguration):
        self.__robot = robot

        # from Titan
        self.speed_motor_0: float = 0.0
        self.speed_motor_1: float = 0.0
        self.speed_motor_2: float = 0.0
        self.speed_motor_3: float = 0.0
        self.speed_motor_4: float = 0.0
        self.speed_motor_5: float = 0.0
        self.speed_motor_6: float = 0.0
        self.speed_motor_7: float = 0.0
        self.enc_motor_0: int = 0
        self.enc_motor_1: int = 0
        self.enc_motor_2: int = 0
        self.enc_motor_3: int = 0
        self.enc_motor_4: int = 0
        self.enc_motor_5: int = 0
        self.enc_motor_6: int = 0
        self.enc_motor_7: int = 0
        self.button_0: bool = False
        self.button_1: bool = False
        self.button_2: bool = False
        self.button_3: bool = False
        self.button_4: bool = False
        self.button_5: bool = False
        self.button_6: bool = False
        self.button_7: bool = False

        # from vmx
        self.yaw: float = 0
        self.ultrasound_1: float = 0
        self.ultrasound_2: float = 0
        self.ultrasound_3: float = 0
        self.ultrasound_4: float = 0
        self.analog_1: int = 0
        self.analog_2: int = 0
        self.analog_3: int = 0
        self.analog_4: int = 0
        self.analog_5: int = 0
        self.analog_6: int = 0
        self.analog_7: int = 0
        self.analog_8: int = 0
        self.led_0: bool = False
        self.led_1: bool = False
        self.led_2: bool = False
        self.led_3: bool = False
        self.servo_values: list = [0.0] * 10

        self.__connection: ConnectionBase = None
        if not self.__robot.on_real_robot:
            self.__connection = ConnectionSim(self.__robot)
            self.__robocad_conn = RobocadConnection()
            self.__robocad_conn.start(self.__connection, self.__robot, self)
        else:
            raise ValueError("CommonRobot could only be used in simulator") 

    def stop(self):
        self.__connection.stop()
        if not self.__robot.on_real_robot:
            if self.__robocad_conn is not None:
                self.__robocad_conn.stop()

    def get_camera(self):
        return self.__connection.get_camera()

    def set_servo_angle(self, angle: float, pin: int):
        dut: float = 0.000666 * angle + 0.05
        self.servo_values[pin] = dut

    def set_servo_pwm(self, pwm: float, pin: int):
        dut: float = pwm
        self.servo_values[pin] = dut

    def disable_servo(self, pin: int):
        self.servo_values[pin] = 0.0
    
class RobocadConnection:
    def __init__(self):
        self.__update_thread = None
        self.__stop_update_thread = False

    def start(self, connection: ConnectionSim, robot: Robot, robot_internal: CommonRobotInternal):
        self.__connection: ConnectionSim = connection
        self.__robot: Robot = robot
        self.__robot_internal: CommonRobotInternal = robot_internal

        self.__robot.power = 12  # todo: control from ConnectionSim from robocad

        self.__stop_update_thread = False
        self.__update_thread = Thread(target=self.__update)
        self.__update_thread.daemon = True
        self.__update_thread.start()

    def stop(self):
        self.__stop_update_thread = True
        if self.__update_thread is not None:
            self.__update_thread.join()
    
    def __set_data(self, values: tuple) -> None:
        self.__connection.set_data(RobocadConnection.join_common_channel(values))

    def __get_data(self) -> tuple:
        return RobocadConnection.parse_common_channel(self.__connection.get_data())
    
    def __update(self):
        while not self.__stop_update_thread:
            # set data
            values = [self.__robot_internal.speed_motor_0,
                      self.__robot_internal.speed_motor_1,
                      self.__robot_internal.speed_motor_2,
                      self.__robot_internal.speed_motor_3,
                      self.__robot_internal.speed_motor_4,
                      self.__robot_internal.speed_motor_5,
                      self.__robot_internal.speed_motor_6,
                      self.__robot_internal.speed_motor_7]
            values.extend(self.__robot_internal.servo_values)
            values.append(1 if self.__robot_internal.led_0 else 0)
            values.append(1 if self.__robot_internal.led_1 else 0)
            values.append(1 if self.__robot_internal.led_2 else 0)
            values.append(1 if self.__robot_internal.led_3 else 0)
            self.__set_data(tuple(values))

            # get data
            values = self.__get_data()
            if len(values) > 0:
                self.__robot_internal.enc_motor_0 = values[0]
                self.__robot_internal.enc_motor_1 = values[1]
                self.__robot_internal.enc_motor_2 = values[2]
                self.__robot_internal.enc_motor_3 = values[3]
                self.__robot_internal.enc_motor_4 = values[4]
                self.__robot_internal.enc_motor_5 = values[5]
                self.__robot_internal.enc_motor_6 = values[6]
                self.__robot_internal.enc_motor_7 = values[7]
                self.__robot_internal.ultrasound_1 = values[8]
                self.__robot_internal.ultrasound_2 = values[9]
                self.__robot_internal.ultrasound_3 = values[10]
                self.__robot_internal.ultrasound_4 = values[11]
                self.__robot_internal.analog_1 = values[12]
                self.__robot_internal.analog_2 = values[13]
                self.__robot_internal.analog_3 = values[14]
                self.__robot_internal.analog_4 = values[15]
                self.__robot_internal.analog_5 = values[16]
                self.__robot_internal.analog_6 = values[17]
                self.__robot_internal.analog_7 = values[18]
                self.__robot_internal.analog_8 = values[19]
                self.__robot_internal.yaw = values[20]

                self.__robot_internal.button_0 = values[21] == 1
                self.__robot_internal.button_1 = values[22] == 1
                self.__robot_internal.button_2 = values[23] == 1
                self.__robot_internal.button_3 = values[24] == 1
                self.__robot_internal.button_4 = values[25] == 1
                self.__robot_internal.button_5 = values[26] == 1
                self.__robot_internal.button_6 = values[27] == 1
                self.__robot_internal.button_7 = values[28] == 1
            
            # задержка для слабых компов
            time.sleep(0.004)
    
    @staticmethod
    def join_common_channel(lst: tuple) -> bytes:
        if len(lst) < 22:
            return b''
        return struct.pack('22f', *lst)
    
    @staticmethod
    def parse_common_channel(data: bytes) -> tuple:
        if len(data) < 76:
            return tuple()
        return struct.unpack('<8i4f8Hf8B', data)
    