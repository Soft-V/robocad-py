import os
import sys
import time
from threading import Thread

from robocad.common import Common
from .shared import TitanStatic
from .shared import LibHolder
from funcad.funcad import Funcad


class TitanCOM:
    th: Thread = None
    stop_th: bool = False

    @classmethod
    def start_com(cls) -> None:
        cls.th: Thread = Thread(target=cls.com_loop)
        cls.th.daemon = True
        cls.th.start()

    @classmethod
    def com_loop(cls) -> None:
        try:
            LibHolder.init()
            LibHolder.init_usb()

            start_time: int = round(time.time() * 10000)
            send_count_time: float = time.time()
            comm_counter = 0
            while not cls.stop_th:
                tx_time: float = time.time() * 1000
                tx_data = cls.set_up_tx_data()
                Common.tx_com_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_data: bytearray = LibHolder.rw_usb(tx_data)

                rx_time: float = time.time() * 1000
                cls.set_up_rx_data(rx_data)
                Common.rx_com_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    Common.com_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.001)
                Common.com_time_dev = round(time.time() * 10000) - start_time
                start_time = round(time.time() * 10000)
        except Exception as e:
            LibHolder.stop_usb()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            Common.logger.write_main_log(str(e))

    @staticmethod
    def set_up_rx_data(data: bytearray) -> None:
        if data[42] != 33:
            if data[0] == 1:
                if data[24] == 111:
                    raw_enc_0: int = (data[2] & 0xff) << 8 | (data[1] & 0xff)
                    raw_enc_1: int = (data[4] & 0xff) << 8 | (data[3] & 0xff)
                    raw_enc_2: int = (data[6] & 0xff) << 8 | (data[5] & 0xff)
                    raw_enc_3: int = (data[8] & 0xff) << 8 | (data[7] & 0xff)
                    TitanCOM.set_up_encoders(raw_enc_0, raw_enc_1, raw_enc_2, raw_enc_3)

                    TitanStatic.limit_l_0 = Funcad.access_bit(data[9], 1)
                    TitanStatic.limit_h_0 = Funcad.access_bit(data[9], 2)
                    TitanStatic.limit_l_1 = Funcad.access_bit(data[9], 3)
                    TitanStatic.limit_h_1 = Funcad.access_bit(data[9], 4)
                    TitanStatic.limit_l_2 = Funcad.access_bit(data[9], 5)
                    TitanStatic.limit_h_2 = Funcad.access_bit(data[9], 6)
                    TitanStatic.limit_l_3 = Funcad.access_bit(data[10], 1)
                    TitanStatic.limit_h_3 = Funcad.access_bit(data[10], 2)

        else:
            Common.logger.write_main_log("received wrong data " + " ".join(map(str, data)))

    @staticmethod
    def set_up_tx_data() -> bytearray:
        tx_data: bytearray = bytearray([0] * 48)
        tx_data[0] = 1

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(TitanStatic.speed_motor_0 / 100 * 65535)))
        tx_data[2] = motor_speeds[2]
        tx_data[3] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(TitanStatic.speed_motor_1 / 100 * 65535)))
        tx_data[4] = motor_speeds[2]
        tx_data[5] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(TitanStatic.speed_motor_2 / 100 * 65535)))
        tx_data[6] = motor_speeds[2]
        tx_data[7] = motor_speeds[3]

        motor_speeds: bytearray = Funcad.int_to_4_bytes(abs(int(TitanStatic.speed_motor_3 / 100 * 65535)))
        tx_data[8] = motor_speeds[2]
        tx_data[9] = motor_speeds[3]

        tx_data[10] = int('1' + ("1" if TitanStatic.speed_motor_0 >= 0 else "0") +
                          ("1" if TitanStatic.speed_motor_1 >= 0 else "0") +
                          ("1" if TitanStatic.speed_motor_2 >= 0 else "0") +
                          ("1" if TitanStatic.speed_motor_3 >= 0 else "0") + '001', 2)

        # third bit is for ProgramIsRunning
        tx_data[11] = int('1' + '0100001', 2)

        tx_data[20] = 222

        return tx_data

    @staticmethod
    def set_up_encoders(enc_0: int, enc_1: int, enc_2: int, enc_3: int) -> None:
        TitanStatic.enc_motor_0 -= TitanCOM.get_normal_diff(enc_0, TitanStatic.raw_enc_motor_0)
        TitanStatic.enc_motor_1 -= TitanCOM.get_normal_diff(enc_1, TitanStatic.raw_enc_motor_1)
        TitanStatic.enc_motor_2 -= TitanCOM.get_normal_diff(enc_2, TitanStatic.raw_enc_motor_2)
        TitanStatic.enc_motor_3 -= TitanCOM.get_normal_diff(enc_3, TitanStatic.raw_enc_motor_3)

        TitanStatic.raw_enc_motor_0 = enc_0
        TitanStatic.raw_enc_motor_1 = enc_1
        TitanStatic.raw_enc_motor_2 = enc_2
        TitanStatic.raw_enc_motor_3 = enc_3

    @staticmethod
    def get_normal_diff(curr: int, last: int) -> int:
        diff: int = curr - last
        if diff > 30000:
            diff = -(last + (65535 - curr))
        elif diff < -30000:
            diff = curr + (65535 - last)
        return diff
