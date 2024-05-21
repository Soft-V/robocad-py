from threading import Thread
import time

import cv2
import numpy as np

from .connection import TalkPort, ListenPort, ParseChannels
from .shared import TitanStatic, VMXStatic
from .connection_base import ConnectionBase


class ConnectionSim(ConnectionBase):
    __port_set_data: int = 65431
    __port_get_data: int = 65432
    __port_camera: int = 65438

    __talk_channel: TalkPort = None
    __listen_channel: ListenPort = None
    __camera_channel: ListenPort = None
    __update_thread: Thread = None
    __stop_update_thread: bool = False

    def start(self) -> None:
        if (self.__talk_channel is None):
            self.__talk_channel = TalkPort(self.__port_set_data)
        self.__talk_channel.start_talking()
        if (self.__listen_channel is None):
            self.__listen_channel = ListenPort(self.__port_get_data)
        self.__listen_channel.start_listening()
        if (self.__camera_channel is None):
            self.__camera_channel = ListenPort(self.__port_camera)
        self.__camera_channel.start_listening()

        self.__stop_update_thread = False
        self.__update_thread = Thread(target=self.__update)
        self.__update_thread.daemon = True
        self.__update_thread.start()

    def stop(self) -> None:
        self.__stop_update_thread = True
        self.__update_thread.join()
        self.__talk_channel.stop_talking()
        self.__listen_channel.stop_listening()
        self.__camera_channel.stop_listening()

    def get_camera(self) -> cv2.typing.MatLike:
        camera_data = self.__camera_channel.out_bytes
        if len(camera_data) == 921600:
            nparr = np.frombuffer(camera_data, np.uint8)
            if nparr.size > 0:
                img_rgb = nparr.reshape(480, 640, 3)
                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                return img_bgr
        return None

    def __set_data(self, values: tuple) -> None:
        self.__talk_channel.out_bytes = ParseChannels.join_studica_channel(values)

    def __get_data(self) -> tuple:
        return ParseChannels.parse_studica_channel(self.__listen_channel.out_bytes)
    
    def __update(self):
        while not self.__stop_update_thread:
            # set data
            values = [TitanStatic.speed_motor_0,
                      TitanStatic.speed_motor_1,
                      TitanStatic.speed_motor_2,
                      TitanStatic.speed_motor_3]
            values.extend(VMXStatic.hcdio_values)
            self.__set_data(tuple(values))

            # get data
            values = self.__get_data()
            if len(values) > 0:
                TitanStatic.enc_motor_0 = values[0]
                TitanStatic.enc_motor_1 = values[1]
                TitanStatic.enc_motor_2 = values[2]
                TitanStatic.enc_motor_3 = values[3]
                VMXStatic.ultrasound_1 = values[4]
                VMXStatic.ultrasound_2 = values[5]
                VMXStatic.analog_1 = values[6]
                VMXStatic.analog_2 = values[7]
                VMXStatic.analog_3 = values[8]
                VMXStatic.analog_4 = values[9]
                VMXStatic.yaw = values[10]

                TitanStatic.limit_h_0 = values[11] == 1
                TitanStatic.limit_l_0 = values[12] == 1
                TitanStatic.limit_h_1 = values[13] == 1
                TitanStatic.limit_l_1 = values[14] == 1
                TitanStatic.limit_h_2 = values[15] == 1
                TitanStatic.limit_l_2 = values[16] == 1
                TitanStatic.limit_h_3 = values[17] == 1
                TitanStatic.limit_l_3 = values[18] == 1

                VMXStatic.flex_0 = values[19] == 1
                VMXStatic.flex_1 = values[20] == 1
                VMXStatic.flex_2 = values[21] == 1
                VMXStatic.flex_3 = values[22] == 1
                VMXStatic.flex_4 = values[23] == 1
                VMXStatic.flex_5 = values[24] == 1
                VMXStatic.flex_6 = values[25] == 1
                VMXStatic.flex_7 = values[26] == 1
            
            # задержка для слабых компов
            time.sleep(0.004)
