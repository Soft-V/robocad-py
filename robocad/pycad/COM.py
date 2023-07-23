import os
import sys
import time
from threading import Thread

import serial

from shufflecad.shared import InfoHolder
from .shared import TitanStatic
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
            ser = serial.Serial(
                port='/dev/ttyACM0',
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )

            start_time: int = round(time.time() * 10000)
            send_count_time: float = time.time()
            comm_counter = 0
            while not cls.stop_th:
                rx_data: bytearray = bytearray(ser.read(48))
                ser.reset_input_buffer()  # reset buffer
                rx_time: int = round(time.time() * 10000)
                TitanCOM.set_up_rx_data(rx_data)
                InfoHolder.rx_com_time_dev = str(round(time.time() * 10000) - rx_time)

                tx_time: int = round(time.time() * 10000)
                tx_data = TitanCOM.set_up_tx_data()
                InfoHolder.tx_com_time_dev = str(round(time.time() * 10000) - tx_time)
                ser.reset_output_buffer()  # reset buffer
                ser.write(tx_data)
                ser.flush()

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    InfoHolder.com_count_dev = str(comm_counter)
                    comm_counter = 0

                time.sleep(0.001)
                InfoHolder.com_time_dev = str(round(time.time() * 10000) - start_time)
                start_time = round(time.time() * 10000)
        except (Exception, serial.SerialException) as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            InfoHolder.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            InfoHolder.logger.write_main_log(str(e))

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
                    # достигнута ли позиция лифта
                    TitanStatic.lift_pos_reached = Funcad.access_bit(data[10], 6)

        else:
            InfoHolder.logger.write_main_log("received wrong data " + " ".join(map(str, data)))

    @staticmethod
    def set_up_tx_data() -> bytearray:
        tx_data: bytearray = bytearray([0] * 48)
        tx_data[0] = 1

        # this cringe was for leds
        tx_data[1] = int('1' + '0000001', 2)

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

        # cringe fuck this shite
        tx_data[11] = int('1' + '0100001', 2)

        tx_data[20] = 222

        # if TitanStatic.speed_motor_0 > 0:
        #     Logger.write_com_log("received wrong data " + " ".join(map(str, tx_data)))

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
