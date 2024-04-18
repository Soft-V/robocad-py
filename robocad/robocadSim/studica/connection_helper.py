from threading import Thread

from .connection import TalkPort, ListenPort, ParseChannels


class ConnectionHelper:
    MAX_DATA_RECEIVE: int = 27
    MAX_DATA_TRANSMIT: int = 14

    __port_set_data: int = 65431
    __port_get_data: int = 65432
    __port_camera: int = 65438

    __talk_channel: TalkPort = None
    __listen_channel: ListenPort = None
    __camera_channel: ListenPort = None
    __update_thread: Thread = None
    __stop_update_thread: bool = False

    @classmethod
    def start_channels(cls) -> None:
        if (cls.__talk_channel is None):
            cls.__talk_channel = TalkPort(cls.__port_set_data)
        cls.__talk_channel.start_talking()
        if (cls.__listen_channel is None):
            cls.__listen_channel = ListenPort(cls.__port_get_data)
        cls.__listen_channel.start_listening()
        if (cls.__camera_channel is None):
            cls.__camera_channel = ListenPort(cls.__port_camera)
        cls.__camera_channel.start_listening()

        cls.__stop_update_thread = False
        cls.__update_thread = Thread(target=cls.__update)
        cls.__update_thread.daemon = True
        cls.__update_thread.start()

    @classmethod
    def stop_channels(cls) -> None:
        cls.__stop_update_thread = True
        cls.__update_thread.join()
        cls.__talk_channel.stop_talking()
        cls.__listen_channel.stop_listening()
        cls.__camera_channel.stop_listening()

    @classmethod
    def set_data(cls, values: tuple) -> None:
        cls.__talk_channel.out_bytes = ParseChannels.join_studica_channel(values)

    @classmethod
    def get_data(cls) -> tuple:
        return ParseChannels.parse_studica_channel(cls.__listen_channel.out_bytes)
    
    @classmethod
    def get_camera(cls) -> bytes:
        return cls.__camera_channel.out_bytes
    
    @classmethod
    def __update(cls):
        while not cls.__stop_update_thread:
            pass
