from threading import Thread
import time

import numpy as np
import cv2

from .connection import TalkPort, ListenPort, ParseChannels
from .shared import TitanStatic, VMXStatic
from .connection_base import ConnectionBase


class ConnectionSim(ConnectionBase):
    __port_set_data: int = 65431
    __port_get_data: int = 65432
    __port_camera: int = 65438

    def __init__(self):
        self.__talk_channel = TalkPort(self.__port_set_data)
        self.__talk_channel.start_talking()
        self.__listen_channel = ListenPort(self.__port_get_data)
        self.__listen_channel.start_listening()
        self.__camera_channel = ListenPort(self.__port_camera)
        self.__camera_channel.start_listening()

    def stop(self) -> None:
        self.__talk_channel.stop_talking()
        self.__listen_channel.stop_listening()
        self.__camera_channel.stop_listening()

    def get_camera(self):
        camera_data = self.__camera_channel.out_bytes
        if len(camera_data) == 921600:
            nparr = np.frombuffer(camera_data, np.uint8)
            if nparr.size > 0:
                img_rgb = nparr.reshape(480, 640, 3)
                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                return img_bgr
        return None
    
    def set_data(self, data: bytes):
        self.__talk_channel.out_bytes = data

    def get_data(self) -> bytes:
        return self.__listen_channel.out_bytes
