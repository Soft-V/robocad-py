from .connection import TalkPort, ListenPort, ParseChannels


class ConnectionHelperVMXTitan:
    MAX_DATA_RECEIVE: int = 27
    MAX_DATA_TRANSMIT: int = 14

    __port_set_data: int = 65431
    __port_get_data: int = 65432
    __port_camera: int = 65438

    def __init__(self) -> None:
        self.__talk_channel = TalkPort(self.__port_set_data)
        self.__listen_channel = ListenPort(self.__port_get_data)
        self.__camera_channel = ListenPort(self.__port_camera, True)

    def start_channels(self) -> None:
        self.__talk_channel.start_talking()
        self.__listen_channel.start_listening()
        self.__camera_channel.start_listening()

    def stop_channels(self) -> None:
        self.__talk_channel.stop_talking()
        self.__listen_channel.stop_listening()
        self.__camera_channel.stop_listening()

    def set_data(self, values: tuple) -> None:
        self.__talk_channel.out_string = ParseChannels.join_float_channel(values)

    def get_data(self) -> tuple:
        return ParseChannels.parse_float_channel(self.__listen_channel.out_string)

    def get_camera(self) -> bytes:
        return self.__camera_channel.out_bytes
