import struct
import sys
import os
import time
from threading import Thread

from funcad.funcad import Funcad

from .common.shared import LibHolder
from .common.robot import Robot
from .common.connection_base import ConnectionBase
from .common.connection_sim import ConnectionSim
from .common.connection_real import ConnectionReal
from .common.updaters import RpiUpdater


class StudicaInternal:
    HCDIO_CONST_ARRAY = [4, 18, 17, 27, 23, 22, 24, 25, 7, 5]

    def __init__(self, robot: Robot):
        self.__robot = robot

        # from Titan
        self.speed_motor_0: float = 0.0
        self.speed_motor_1: float = 0.0
        self.speed_motor_2: float = 0.0
        self.speed_motor_3: float = 0.0
        self.enc_motor_0: int = 0
        self.enc_motor_1: int = 0
        self.enc_motor_2: int = 0
        self.enc_motor_3: int = 0
        self.raw_enc_motor_0: int = 0
        self.raw_enc_motor_1: int = 0
        self.raw_enc_motor_2: int = 0
        self.raw_enc_motor_3: int = 0
        self.limit_l_0: bool = False
        self.limit_h_0: bool = False
        self.limit_l_1: bool = False
        self.limit_h_1: bool = False
        self.limit_l_2: bool = False
        self.limit_h_2: bool = False
        self.limit_l_3: bool = False
        self.limit_h_3: bool = False

        # from vmx
        self.yaw: float = 0
        self.yaw_unlim: float = 0
        self.calib_imu: bool = False
        self.ultrasound_1: float = 0
        self.ultrasound_2: float = 0
        self.analog_1: int = 0
        self.analog_2: int = 0
        self.analog_3: int = 0
        self.analog_4: int = 0
        self.flex_0: bool = False
        self.flex_1: bool = False
        self.flex_2: bool = False
        self.flex_3: bool = False
        self.flex_4: bool = False
        self.flex_5: bool = False
        self.flex_6: bool = False
        self.flex_7: bool = False
        self.hcdio_values: list = [0.0] * 10

        self.__connection: ConnectionBase = None
        if not self.__robot.on_real_robot:
            self.__connection = ConnectionSim(self.__robot)
            self.__robocad_conn = RobocadConnection()
            self.__robocad_conn.start(self.__connection, self.__robot, self)
        else:
            updater = RpiUpdater(self.__robot)
            self.__connection = ConnectionReal(self.__robot, updater)
            self.__titan = TitanCOM()
            self.__titan.start_com(self.__connection, self.__robot, self)
            self.__vmx = VMXSPI()
            self.__vmx.start_spi(self.__connection, self.__robot, self)

    def stop(self):
        self.__connection.stop()
        if not self.__robot.on_real_robot:
            if self.__robocad_conn is not None:
                self.__robocad_conn.stop()
        else:
            if self.__titan is not None:
                self.__titan.stop()
            if self.__vmx is not None:
                self.__vmx.stop()

    def get_camera(self):
        return self.__connection.get_camera()

    def set_servo_angle(self, angle: float, pin: int):
        dut: float = 0.000666 * angle + 0.05
        self.hcdio_values[pin] = dut
        self.echo_to_file(str(self.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    def set_led_state(self, state: bool, pin: int):
        dut: float = 0.2 if state else 0.0
        self.hcdio_values[pin] = dut
        self.echo_to_file(str(self.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    def set_servo_pwm(self, pwm: float, pin: int):
        dut: float = pwm
        self.hcdio_values[pin] = dut
        self.echo_to_file(str(self.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    def disable_servo(self, pin: int):
        self.hcdio_values[pin] = 0.0
        self.echo_to_file(str(self.HCDIO_CONST_ARRAY[pin]) + "=" + "0.0")

    def echo_to_file(self, st: str):
        if not self.__robot.on_real_robot:
            return None
        original_stdout = sys.stdout
        with open('/dev/pi-blaster', 'w') as f:
            sys.stdout = f  # Change the standard output to the file we created.
            print(st)
            sys.stdout = original_stdout  # Reset the standard output to its original value
    
class RobocadConnection:
    def __init__(self):
        self.__update_thread = None
        self.__stop_update_thread = False

    def start(self, connection: ConnectionSim, robot: Robot, robot_internal: StudicaInternal):
        self.__connection: ConnectionSim = connection
        self.__robot: Robot = robot
        self.__robot_internal: StudicaInternal = robot_internal

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
        self.__connection.set_data(RobocadConnection.join_studica_channel(values))

    def __get_data(self) -> tuple:
        return RobocadConnection.parse_studica_channel(self.__connection.get_data())
    
    def __update(self):
        while not self.__stop_update_thread:
            # set data
            values = [self.__robot_internal.speed_motor_0,
                      self.__robot_internal.speed_motor_1,
                      self.__robot_internal.speed_motor_2,
                      self.__robot_internal.speed_motor_3]
            values.extend(self.__robot_internal.hcdio_values)
            self.__set_data(tuple(values))

            # get data
            values = self.__get_data()
            if len(values) > 0:
                self.__robot_internal.enc_motor_0 = values[0]
                self.__robot_internal.enc_motor_1 = values[1]
                self.__robot_internal.enc_motor_2 = values[2]
                self.__robot_internal.enc_motor_3 = values[3]
                self.__robot_internal.ultrasound_1 = values[4]
                self.__robot_internal.ultrasound_2 = values[5]
                self.__robot_internal.analog_1 = values[6]
                self.__robot_internal.analog_2 = values[7]
                self.__robot_internal.analog_3 = values[8]
                self.__robot_internal.analog_4 = values[9]
                self.__robot_internal.yaw = values[10]

                self.__robot_internal.limit_h_0 = values[11] == 1
                self.__robot_internal.limit_l_0 = values[12] == 1
                self.__robot_internal.limit_h_1 = values[13] == 1
                self.__robot_internal.limit_l_1 = values[14] == 1
                self.__robot_internal.limit_h_2 = values[15] == 1
                self.__robot_internal.limit_l_2 = values[16] == 1
                self.__robot_internal.limit_h_3 = values[17] == 1
                self.__robot_internal.limit_l_3 = values[18] == 1

                self.__robot_internal.flex_0 = values[19] == 1
                self.__robot_internal.flex_1 = values[20] == 1
                self.__robot_internal.flex_2 = values[21] == 1
                self.__robot_internal.flex_3 = values[22] == 1
                self.__robot_internal.flex_4 = values[23] == 1
                self.__robot_internal.flex_5 = values[24] == 1
                self.__robot_internal.flex_6 = values[25] == 1
                self.__robot_internal.flex_7 = values[26] == 1
            
            # задержка для слабых компов
            time.sleep(0.004)
    
    @staticmethod
    def join_studica_channel(lst: tuple) -> bytes:
        if len(lst) < 14:
            return b''
        return struct.pack('14f', *lst)
    
    @staticmethod
    def parse_studica_channel(data: bytes) -> tuple:
        if len(data) < 52:
            return tuple()
        return struct.unpack('<4i2f4Hf16B', data)
    
class TitanCOM:
    def __init__(self):
        self.__th: Thread = None
        self.__stop_th: bool = False

    def start_com(self, connection: ConnectionReal, robot: Robot, robot_internal: StudicaInternal) -> None:
        self.__connection: ConnectionReal = connection
        self.__robot: Robot = robot
        self.__robot_internal: StudicaInternal = robot_internal

        self.__stop_th: bool = False
        self.__th: Thread = Thread(target=self.com_loop)
        self.__th.daemon = True
        self.__th.start()

    def stop(self):
        self.__stop_th = True
        if self.__th is not None:
            self.__th.join()

    def com_loop(self) -> None:
        try:
            com_result = self.__connection.com_ini("/dev/ttyACM0", 115200)
            if com_result != 0:
                self.__robot.write_log("Failed to open COM")
                return

            start_time: int = round(time.time() * 10000)
            send_count_time: float = time.time()
            comm_counter = 0
            while not self.__stop_th:
                tx_time: float = time.time() * 1000
                tx_data = self.set_up_tx_data()
                self.__robot.__tx_com_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_data: bytearray = self.__connection.com_rw(tx_data)

                rx_time: float = time.time() * 1000
                self.set_up_rx_data(rx_data)
                self.__robot.__rx_com_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    self.__robot.__com_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.001)
                self.__robot.__com_time_dev = round(time.time() * 10000) - start_time
                start_time = round(time.time() * 10000)
        except Exception as e:
            self.__connection.com_stop()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            self.__robot.write_log(str(e))

    def set_up_rx_data(self, data: bytearray) -> None:
        if data[42] != 33:
            if data[0] == 1:
                if data[24] == 111:
                    raw_enc_0: int = (data[2] & 0xff) << 8 | (data[1] & 0xff)
                    raw_enc_1: int = (data[4] & 0xff) << 8 | (data[3] & 0xff)
                    raw_enc_2: int = (data[6] & 0xff) << 8 | (data[5] & 0xff)
                    raw_enc_3: int = (data[8] & 0xff) << 8 | (data[7] & 0xff)
                    self.set_up_encoders(raw_enc_0, raw_enc_1, raw_enc_2, raw_enc_3)

                    self.__robot_internal.limit_l_0 = Funcad.access_bit(data[9], 1)
                    self.__robot_internal.limit_h_0 = Funcad.access_bit(data[9], 2)
                    self.__robot_internal.limit_l_1 = Funcad.access_bit(data[9], 3)
                    self.__robot_internal.limit_h_1 = Funcad.access_bit(data[9], 4)
                    self.__robot_internal.limit_l_2 = Funcad.access_bit(data[9], 5)
                    self.__robot_internal.limit_h_2 = Funcad.access_bit(data[9], 6)
                    self.__robot_internal.limit_l_3 = Funcad.access_bit(data[10], 1)
                    self.__robot_internal.limit_h_3 = Funcad.access_bit(data[10], 2)

        else:
            self.__robot.write_log("received wrong data " + " ".join(map(str, data)))

    def set_up_tx_data(self) -> bytearray:
        tx_data: bytearray = bytearray([0] * 48)
        tx_data[0] = 1

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(self.__robot_internal.speed_motor_0 / 100 * 65535)))
        tx_data[2] = motor_speeds[2]
        tx_data[3] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(self.__robot_internal.speed_motor_1 / 100 * 65535)))
        tx_data[4] = motor_speeds[2]
        tx_data[5] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(self.__robot_internal.speed_motor_2 / 100 * 65535)))
        tx_data[6] = motor_speeds[2]
        tx_data[7] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(self.__robot_internal.speed_motor_3 / 100 * 65535)))
        tx_data[8] = motor_speeds[2]
        tx_data[9] = motor_speeds[3]

        tx_data[10] = int('1' + ("1" if self.__robot_internal.speed_motor_0 >= 0 else "0") +
                                ("1" if self.__robot_internal.speed_motor_1 >= 0 else "0") +
                                ("1" if self.__robot_internal.speed_motor_2 >= 0 else "0") +
                                ("1" if self.__robot_internal.speed_motor_3 >= 0 else "0") + '001', 2)

        # third bit is for ProgramIsRunning
        tx_data[11] = int('1' + '0100001', 2)

        tx_data[20] = 222

        return tx_data

    def set_up_encoders(self, enc_0: int, enc_1: int, enc_2: int, enc_3: int) -> None:
        self.__robot_internal.enc_motor_0 -= TitanCOM.get_normal_diff(enc_0, self.__robot_internal.raw_enc_motor_0)
        self.__robot_internal.enc_motor_1 -= TitanCOM.get_normal_diff(enc_1, self.__robot_internal.raw_enc_motor_1)
        self.__robot_internal.enc_motor_2 -= TitanCOM.get_normal_diff(enc_2, self.__robot_internal.raw_enc_motor_2)
        self.__robot_internal.enc_motor_3 -= TitanCOM.get_normal_diff(enc_3, self.__robot_internal.raw_enc_motor_3)

        self.__robot_internal.raw_enc_motor_0 = enc_0
        self.__robot_internal.raw_enc_motor_1 = enc_1
        self.__robot_internal.raw_enc_motor_2 = enc_2
        self.__robot_internal.raw_enc_motor_3 = enc_3

    @staticmethod
    def get_normal_diff(curr: int, last: int) -> int:
        diff: int = curr - last
        if diff > 30000:
            diff = -(last + (65535 - curr))
        elif diff < -30000:
            diff = curr + (65535 - last)
        return diff
    
class VMXSPI:
    def __init__(self):
        self.__th: Thread = None
        self.__stop_th: bool = False

    def start_spi(self, connection: ConnectionReal, robot: Robot, robot_internal: StudicaInternal) -> None:
        self.__connection: ConnectionReal = connection
        self.__robot: Robot = robot
        self.__robot_internal: StudicaInternal = robot_internal

        self.__toggler: int = 0
        self.__stop_th: bool = False
        self.__th: Thread = Thread(target=self.spi_loop)
        self.__th.daemon = True
        self.__th.start()

    def stop(self):
        self.__stop_th = True
        if self.__th is not None:
            self.__th.join()

    def spi_loop(self) -> None:
        try:
            spi_result = self.__connection.spi_ini("/dev/spidev1.2", 2, 1000000, 0)
            if spi_result != 0:
                self.__robot.write_log("Failed to open SPI")
                return

            start_time: float = time.time() * 1000
            send_count_time: float = time.time()
            comm_counter = 0
            while not self.__stop_th:
                tx_time: float = time.time() * 1000
                tx_list = self.set_up_tx_data()
                self.__robot.__tx_spi_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_list: bytearray = self.__connection.spi_rw(tx_list)

                rx_time: float = time.time() * 1000
                self.set_up_rx_data(rx_list)
                self.__robot.__rx_spi_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    self.__robot.__spi_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.002)
                self.__robot.__spi_time_dev = round(time.time() * 1000 - start_time, 2)
                start_time = time.time() * 1000
        except (Exception, EOFError) as e:
            self.__connection.spi_stop()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            self.__robot.write_log(str(e))

    def set_up_rx_data(self, data: bytearray) -> None:
        if data[0] == 1:
            yaw_ui: int = (data[2] & 0xff) << 8 | (data[1] & 0xff)
            us1_ui: int = (data[4] & 0xff) << 8 | (data[3] & 0xff)
            self.__robot_internal.ultrasound_1 = us1_ui / 100
            us2_ui: int = (data[6] & 0xff) << 8 | (data[5] & 0xff)
            self.__robot_internal.ultrasound_2 = us2_ui / 100

            power: float = ((data[8] & 0xff) << 8 | (data[7] & 0xff)) / 100
            self.__robot.power = power

            # calc yaw unlim
            new_yaw = (yaw_ui / 100) * (1 if Funcad.access_bit(data[9], 1) else -1)
            self.calc_yaw_unlim(new_yaw, self.__robot_internal.yaw)
            self.__robot_internal.yaw = new_yaw

            self.__robot_internal.flex_0 = Funcad.access_bit(data[9], 2)
            self.__robot_internal.flex_1 = Funcad.access_bit(data[9], 3)
            self.__robot_internal.flex_2 = Funcad.access_bit(data[9], 4)
            self.__robot_internal.flex_3 = Funcad.access_bit(data[9], 5)
            self.__robot_internal.flex_4 = Funcad.access_bit(data[9], 6)
        elif data[0] == 2:
            self.__robot_internal.analog_1 = (data[2] & 0xff) << 8 | (data[1] & 0xff)
            self.__robot_internal.analog_2 = (data[4] & 0xff) << 8 | (data[3] & 0xff)
            self.__robot_internal.analog_3 = (data[6] & 0xff) << 8 | (data[5] & 0xff)
            self.__robot_internal.analog_4 = (data[8] & 0xff) << 8 | (data[7] & 0xff)

            self.__robot_internal.flex_5 = Funcad.access_bit(data[9], 1)
            self.__robot_internal.flex_6 = Funcad.access_bit(data[9], 2)
            self.__robot_internal.flex_7 = Funcad.access_bit(data[9], 3)

    def set_up_tx_data(self) -> bytearray:
        tx_list: bytearray = bytearray([0x00] * 10)

        if self.__toggler == 0:
            tx_list[0] = 1

            tx_list[9] = 222
        return tx_list

    def calc_yaw_unlim(self, new_yaw: float, old_yaw: float):
        delta_yaw = new_yaw - old_yaw
        if delta_yaw < -180:
            delta_yaw = 180 - old_yaw
            delta_yaw += 180 + new_yaw
        elif delta_yaw > 180:
            delta_yaw = (180 + old_yaw) * -1
            delta_yaw += (180 - new_yaw) * -1
        self.__robot_internal.yaw_unlim += delta_yaw