from .connection import TalkPort, ListenPort, ParseChannels


class ConnectionHelper:
    # для connection helper
    CONN_OTHER: int = 0x0001
    CONN_MOTORS_AND_ENCS: int = 0x0002
    CONN_OMS: int = 0x0004
    CONN_RESETS: int = 0x0008
    CONN_SENS: int = 0x0010
    CONN_BUTTONS: int = 0x0020
    CONN_CAMERA: int = 0x0040
    CONN_ALL: int = 0x00ff

    __port_other: int = 65431
    __port_motors: int = 65432
    __port_oms: int = 65433
    __port_resets: int = 65434
    __port_encs: int = 65435
    __port_sens: int = 65436
    __port_buttons: int = 65437
    __port_camera: int = 65438

    def __init__(self, setting: int) -> None:
        self.__setting = setting

        if self.__setting & self.CONN_OTHER:
            self.__other_channel = TalkPort(self.__port_other)
        if self.__setting & self.CONN_MOTORS_AND_ENCS:
            self.__motors_channel = TalkPort(self.__port_motors)
            self.__encs_channel = ListenPort(self.__port_encs)
        if self.__setting & self.CONN_OMS:
            self.__oms_channel = TalkPort(self.__port_oms)
        if self.__setting & self.CONN_RESETS:
            self.__resets_channel = TalkPort(self.__port_resets)
        if self.__setting & self.CONN_SENS:
            self.__sensors_channel = ListenPort(self.__port_sens)
        if self.__setting & self.CONN_BUTTONS:
            self.__buttons_channel = ListenPort(self.__port_buttons)
        if self.__setting & self.CONN_CAMERA:
            self.__camera_channel = ListenPort(self.__port_camera, True)

    def start_channels(self) -> None:
        if self.__setting & self.CONN_OTHER:
            self.__other_channel.start_talking()
        if self.__setting & self.CONN_MOTORS_AND_ENCS:
            self.__motors_channel.start_talking()
            self.__encs_channel.start_listening()
        if self.__setting & self.CONN_OMS:
            self.__oms_channel.start_talking()
        if self.__setting & self.CONN_RESETS:
            self.__resets_channel.start_talking()
        if self.__setting & self.CONN_SENS:
            self.__sensors_channel.start_listening()
        if self.__setting & self.CONN_BUTTONS:
            self.__buttons_channel.start_listening()
        if self.__setting & self.CONN_CAMERA:
            self.__camera_channel.start_listening()

    def stop_channels(self) -> None:
        if self.__setting & self.CONN_OTHER:
            self.__other_channel.stop_talking()
        if self.__setting & self.CONN_MOTORS_AND_ENCS:
            self.__motors_channel.stop_talking()
            self.__encs_channel.stop_listening()
        if self.__setting & self.CONN_OMS:
            self.__oms_channel.stop_talking()
        if self.__setting & self.CONN_RESETS:
            self.__resets_channel.stop_talking()
        if self.__setting & self.CONN_SENS:
            self.__sensors_channel.stop_listening()
        if self.__setting & self.CONN_BUTTONS:
            self.__buttons_channel.stop_listening()
        if self.__setting & self.CONN_CAMERA:
            self.__camera_channel.stop_listening()

    def set_other(self, values: tuple) -> None:
        self.__other_channel.out_string = ParseChannels.join_float_channel(values)

    def set_motors(self, values: tuple) -> None:
        self.__motors_channel.out_string = ParseChannels.join_float_channel(values)

    def set_oms(self, values: tuple) -> None:
        self.__oms_channel.out_string = ParseChannels.join_float_channel(values)

    def set_resets(self, values: tuple) -> None:
        self.__resets_channel.out_string = ParseChannels.join_bool_channel(values)

    def get_encs(self) -> tuple:
        return ParseChannels.parse_float_channel(self.__encs_channel.out_string)

    def get_sens(self) -> tuple:
        return ParseChannels.parse_float_channel(self.__sensors_channel.out_string)

    def get_buttons(self) -> tuple:
        return ParseChannels.parse_bool_channel(self.__buttons_channel.out_string)

    def get_camera(self) -> bytes:
        return self.__camera_channel.out_bytes
