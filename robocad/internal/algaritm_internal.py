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
from .common.updaters import ElveesUpdater


class AlgaritmInternal:
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
        self.limit_l_0: bool = False
        self.limit_h_0: bool = False
        self.limit_l_1: bool = False
        self.limit_h_1: bool = False
        self.limit_l_2: bool = False
        self.limit_h_2: bool = False
        self.limit_l_3: bool = False
        self.limit_h_3: bool = False

        self.__connection: ConnectionBase = None
        if not self.__robot.on_real_robot:
            pass
            # self.__connection = ConnectionSim(self.__robot)
            # self.__robocad_conn = RobocadConnection()
            # self.__robocad_conn.start(self.__connection, self.__robot, self)
        else:
            updater = ElveesUpdater(self.__robot)
            self.__connection = ConnectionReal(self.__robot, updater, '/home/elvees', False)
            self.__titan = TitanCOM()
            self.__titan.start_com(self.__connection, self.__robot, self)
            self.__vmx = VMXSPI()
            self.__vmx.start_spi(self.__connection, self.__robot, self)

    def stop(self):
        self.__connection.stop()
        if not self.__robot.on_real_robot:
            pass
            # if self.__robocad_conn is not None:
                # self.__robocad_conn.stop()
        else:
            if self.__titan is not None:
                self.__titan.stop()
            if self.__vmx is not None:
                self.__vmx.stop()

    def get_camera(self):
        return self.__connection.get_camera()
    
class TitanCOM:
    def __init__(self):
        self.__th: Thread = None
        self.__stop_th: bool = False

    def start_com(self, connection: ConnectionReal, robot: Robot, robot_internal: AlgaritmInternal) -> None:
        self.__connection: ConnectionReal = connection
        self.__robot: Robot = robot
        self.__robot_internal: AlgaritmInternal = robot_internal

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
                self.__robot.robot_info.tx_com_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_data: bytearray = self.__connection.com_rw(tx_data)

                rx_time: float = time.time() * 1000
                self.set_up_rx_data(rx_data)
                self.__robot.robot_info.rx_com_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    self.__robot.robot_info.com_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.001)
                self.__robot.robot_info.com_time_dev = round(time.time() * 10000) - start_time
                start_time = round(time.time() * 10000)
        except Exception as e:
            self.__connection.com_stop()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            self.__robot.write_log(str(e))

    def set_up_rx_data(self, data: bytearray) -> None:
        if data[0] == 1:
            if data[18] == 222:
                self.__robot_internal.enc_motor_0 = ((data[4] & 0xff) << 24) | ((data[3] & 0xff) << 16) | ((data[2] & 0xff) << 8) | (data[1] & 0xff)
                self.__robot_internal.enc_motor_1 = ((data[8] & 0xff) << 24) | ((data[7] & 0xff) << 16) | ((data[6] & 0xff) << 8) | (data[5] & 0xff)
                self.__robot_internal.enc_motor_2 = ((data[12] & 0xff) << 24) | ((data[11] & 0xff) << 16) | ((data[10] & 0xff) << 8) | (data[9] & 0xff)
                self.__robot_internal.enc_motor_3 = ((data[16] & 0xff) << 24) | ((data[15] & 0xff) << 16) | ((data[14] & 0xff) << 8) | (data[13] & 0xff)

                self.__robot_internal.limit_l_0 = Funcad.access_bit(data[9], 0)
                self.__robot_internal.limit_h_0 = Funcad.access_bit(data[9], 1)
                self.__robot_internal.limit_l_1 = Funcad.access_bit(data[9], 2)
                self.__robot_internal.limit_h_1 = Funcad.access_bit(data[9], 3)
                self.__robot_internal.limit_l_2 = Funcad.access_bit(data[9], 4)
                self.__robot_internal.limit_h_2 = Funcad.access_bit(data[9], 5)
                self.__robot_internal.limit_l_3 = Funcad.access_bit(data[9], 6)
                self.__robot_internal.limit_h_3 = Funcad.access_bit(data[9], 7)

        else:
            self.__robot.write_log("received wrong data " + " ".join(map(str, data)))

    def set_up_tx_data(self) -> bytearray:
        tx_data: bytearray = bytearray([0] * 48)
        tx_data[0] = 1

        tx_data[1] = int(self.__robot_internal.speed_motor_0).to_bytes(1, 'big', signed = True)[0]
        tx_data[2] = int(self.__robot_internal.speed_motor_1).to_bytes(1, 'big', signed = True)[0]
        tx_data[3] = int(self.__robot_internal.speed_motor_2).to_bytes(1, 'big', signed = True)[0]
        tx_data[4] = int(self.__robot_internal.speed_motor_3).to_bytes(1, 'big', signed = True)[0]

        # for ProgramIsRunning
        tx_data[5] = 1

        tx_data[20] = 222

        return tx_data
    
class VMXSPI:
    def __init__(self):
        self.__th: Thread = None
        self.__stop_th: bool = False

    def start_spi(self, connection: ConnectionReal, robot: Robot, robot_internal: AlgaritmInternal) -> None:
        self.__connection: ConnectionReal = connection
        self.__robot: Robot = robot
        self.__robot_internal: AlgaritmInternal = robot_internal

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
                self.__robot.robot_info.tx_spi_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_list: bytearray = self.__connection.spi_rw(tx_list)

                rx_time: float = time.time() * 1000
                self.set_up_rx_data(rx_list)
                self.__robot.robot_info.rx_spi_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    self.__robot.robot_info.spi_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.002)
                self.__robot.robot_info.spi_time_dev = round(time.time() * 1000 - start_time, 2)
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