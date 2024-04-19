import os
import sys
import time
from threading import Thread

from robocad.common import Common
from .shared import VMXStatic
from .shared import LibHolder
from funcad.funcad import Funcad


class VMXSPI:
    toggler: int = 0

    th: Thread = None
    stop_th: bool = False

    @classmethod
    def start_spi(cls) -> None:
        cls.th: Thread = Thread(target=cls.spi_loop)
        cls.th.daemon = True
        cls.th.start()

    @classmethod
    def spi_loop(cls) -> None:
        try:
            LibHolder.init()
            LibHolder.init_spi()

            start_time: float = time.time() * 1000
            send_count_time: float = time.time()
            comm_counter = 0
            while not cls.stop_th:
                tx_time: float = time.time() * 1000
                tx_list = cls.set_up_tx_data()
                Common.tx_spi_time_dev = round(time.time() * 1000 - tx_time, 2)

                rx_list: bytearray = LibHolder.rw_spi(tx_list)

                rx_time: float = time.time() * 1000
                cls.set_up_rx_data(rx_list)
                Common.rx_spi_time_dev = round(time.time() * 1000 - rx_time, 2)

                comm_counter += 1
                if time.time() - send_count_time > 1:
                    send_count_time = time.time()
                    Common.spi_count_dev = comm_counter
                    comm_counter = 0

                time.sleep(0.002)
                Common.spi_time_dev = round(time.time() * 1000 - start_time, 2)
                start_time = time.time() * 1000
        except (Exception, EOFError) as e:
            LibHolder.stop_spi()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
            Common.logger.write_main_log(str(e))

    @classmethod
    def set_up_rx_data(cls, data: bytearray) -> None:
        if data[0] == 1:
            yaw_ui: int = (data[2] & 0xff) << 8 | (data[1] & 0xff)
            us1_ui: int = (data[4] & 0xff) << 8 | (data[3] & 0xff)
            VMXStatic.ultrasound_1 = us1_ui / 100
            us2_ui: int = (data[6] & 0xff) << 8 | (data[5] & 0xff)
            VMXStatic.ultrasound_2 = us2_ui / 100

            power: float = ((data[8] & 0xff) << 8 | (data[7] & 0xff)) / 100
            Common.power = power

            # calc yaw unlim
            new_yaw = (yaw_ui / 100) * (1 if Funcad.access_bit(data[9], 1) else -1)
            cls.calc_yaw_unlim(new_yaw, VMXStatic.yaw)
            VMXStatic.yaw = new_yaw

            VMXStatic.flex_0 = Funcad.access_bit(data[9], 2)
            VMXStatic.flex_1 = Funcad.access_bit(data[9], 3)
            VMXStatic.flex_2 = Funcad.access_bit(data[9], 4)
            VMXStatic.flex_3 = Funcad.access_bit(data[9], 5)
            VMXStatic.flex_4 = Funcad.access_bit(data[9], 6)
        elif data[0] == 2:
            VMXStatic.analog_1 = (data[2] & 0xff) << 8 | (data[1] & 0xff)
            VMXStatic.analog_2 = (data[4] & 0xff) << 8 | (data[3] & 0xff)
            VMXStatic.analog_3 = (data[6] & 0xff) << 8 | (data[5] & 0xff)
            VMXStatic.analog_4 = (data[8] & 0xff) << 8 | (data[7] & 0xff)

            VMXStatic.flex_5 = Funcad.access_bit(data[9], 1)
            VMXStatic.flex_6 = Funcad.access_bit(data[9], 2)
            VMXStatic.flex_7 = Funcad.access_bit(data[9], 3)

    @classmethod
    def set_up_tx_data(cls) -> bytearray:
        tx_list: bytearray = bytearray([0x00] * 10)

        if cls.toggler == 0:
            tx_list[0] = 1

            tx_list[9] = 222
        return tx_list

    @staticmethod
    def calc_yaw_unlim(new_yaw: float, old_yaw: float):
        delta_yaw = new_yaw - old_yaw
        if delta_yaw < -180:
            delta_yaw = 180 - old_yaw
            delta_yaw += 180 + new_yaw
        elif delta_yaw > 180:
            delta_yaw = (180 + old_yaw) * -1
            delta_yaw += (180 - new_yaw) * -1
        VMXStatic.yaw_unlim += delta_yaw
