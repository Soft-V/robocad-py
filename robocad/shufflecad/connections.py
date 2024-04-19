import os
import sys
import io
import socket
import struct
import time
from threading import Thread

from robocad.common import Common
from .shufflecad_holder import CameraVariable, ShufflecadHolder, ShuffleVariable

class ListenPort:
    def __init__(self, port: int, event_handler=None, delay: float = 0.004):
        self.__port = port

        # other
        self.__stop_thread = False
        self.out_string = 'null'
        self.out_bytes = b'null'

        self.__sct = None
        self.__thread = None

        self.__event_handler = event_handler
        self.__delay = delay

    def event_call(self):
        if self.__event_handler is not None:
            self.__event_handler()

    def start_listening(self):
        self.__thread = Thread(target=self.listening, args=())
        self.__thread.start()

    def listening(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.__sct.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sct.bind(('0.0.0.0', self.__port))
        self.__sct.listen(1)

        connection_out = self.__sct.accept()[0].makefile('rwb')
        handler = SplitFrames(connection_out)
        while not self.__stop_thread:
            try:
                handler.write("Waiting for data".encode("utf-8"))
                self.out_string = handler.read().decode("utf-8")

                self.event_call()

                # задержка для слабых компов
                time.sleep(self.__delay)
            except (ConnectionAbortedError, BrokenPipeError) as e:
                # возникает при отключении сокета
                exc_type, exc_obj, exc_tb = sys.exc_info()
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                Common.logger.write_main_log(str(e))
                break
        self.__sct.shutdown(socket.SHUT_RDWR)
        self.__sct.close()

    def reset_out(self):
        self.out_string = 'null'
        self.out_bytes = b'null'

    def stop_listening(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception) as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                Common.logger.write_main_log(str(e))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 0.2:
                        try:
                            self.__sct.close()
                        except (OSError, Exception) as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            Common.logger.write_main_log(" ".join(map(str,
                                                                          [exc_type, file_name, exc_tb.tb_lineno])))
                            Common.logger.write_main_log(str(e))
                        st_time = time.time()


class TalkPort:
    def __init__(self, port: int, event_handler=None, delay: float = 0.004, is_camera: bool = False):
        self.__port = port

        # other
        self.__stop_thread = False
        self.out_string = 'null'
        self.out_bytes = b'null'

        self.str_from_client = '-1'

        self.__sct = None
        self.__thread = None

        self.__is_camera = is_camera

        self.__event_handler = event_handler
        self.__delay = delay

    def event_call(self):
        if self.__event_handler is not None:
            self.__event_handler()

    def start_talking(self):
        self.__thread = Thread(target=self.talking, args=())
        self.__thread.start()

    def talking(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.__sct.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sct.bind(('0.0.0.0', self.__port))
        self.__sct.listen(1)

        connection_out = self.__sct.accept()[0].makefile('rwb')
        handler = SplitFrames(connection_out)
        while not self.__stop_thread:
            try:
                self.event_call()

                if self.__is_camera:
                    handler.write(self.out_string.encode("utf-8"))
                    _ = handler.read()
                    handler.write(self.out_bytes)
                    self.str_from_client = handler.read()
                else:
                    handler.write(self.out_string.encode("utf-8"))
                    self.str_from_client = handler.read().decode("utf-8")

                # задержка для слабых компов
                time.sleep(self.__delay)
            except (ConnectionAbortedError, BrokenPipeError) as e:
                # возникает при отключении сокета
                exc_type, exc_obj, exc_tb = sys.exc_info()
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                Common.logger.write_main_log(str(e))
                break
        self.__sct.shutdown(socket.SHUT_RDWR)
        self.__sct.close()

    def reset_out(self):
        self.out_string = 'null'
        self.str_from_client = '-1'

    def stop_talking(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception) as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Common.logger.write_main_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                Common.logger.write_main_log(str(e))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 0.2:
                        try:
                            self.__sct.close()
                        except (OSError, Exception) as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            Common.logger.write_main_log(" ".join(map(str,
                                                                          [exc_type, file_name, exc_tb.tb_lineno])))
                            Common.logger.write_main_log(str(e))
                        st_time = time.time()


class ConnectionHelper:
    out_variables_channel: TalkPort
    in_variables_channel: ListenPort
    chart_variables_channel: TalkPort
    outcad_variables_channel: TalkPort
    rpi_variables_channel: TalkPort
    camera_variables_channel: TalkPort
    joy_variables_channel: ListenPort

    # @classmethod
    # def add_var(cls, var):
    #     InfoHolder.variables_array.append(var)
    #     return var
    #
    # @classmethod
    # def add_camera_var(cls, var):
    #     InfoHolder.camera_variables_array.append(var)
    #     return var

    @classmethod
    def init_and_start(cls):
        cls.out_variables_channel = TalkPort(63253, cls.on_out_vars, 0.004)
        cls.in_variables_channel = ListenPort(63258, cls.on_in_vars, 0.004)
        cls.chart_variables_channel = TalkPort(63255, cls.on_chart_vars, 0.002)
        cls.outcad_variables_channel = TalkPort(63257, cls.on_outcad_vars, 0.1)
        cls.rpi_variables_channel = TalkPort(63256, cls.on_rpi_vars, 0.5)
        cls.camera_variables_channel = TalkPort(63254, cls.on_camera_vars, 0.03, True)
        cls.joy_variables_channel = ListenPort(63259, cls.on_joy_vars, 0.004)

        cls.start()

    @classmethod
    def start(cls):
        cls.out_variables_channel.start_talking()
        cls.in_variables_channel.start_listening()
        cls.chart_variables_channel.start_talking()
        cls.outcad_variables_channel.start_talking()
        cls.rpi_variables_channel.start_talking()
        cls.camera_variables_channel.start_talking()
        cls.joy_variables_channel.start_listening()

    @classmethod
    def stop(cls):
        cls.out_variables_channel.stop_talking()
        cls.in_variables_channel.stop_listening()
        cls.chart_variables_channel.stop_talking()
        cls.outcad_variables_channel.stop_talking()
        cls.rpi_variables_channel.stop_talking()
        cls.camera_variables_channel.stop_talking()
        cls.joy_variables_channel.stop_listening()

    @classmethod
    def on_out_vars(cls):
        without_charts = [i for i in ShufflecadHolder.variables_array if i.type_ != ShuffleVariable.CHART_TYPE]
        if len(without_charts) > 0:
            strings = ["{0};{1};{2};{3}".format(i.name, i.value, i.type_, i.direction) for i in without_charts]
            cls.out_variables_channel.out_string = "&".join(strings)
        else:
            cls.out_variables_channel.out_string = "null"

    @classmethod
    def on_in_vars(cls):
        if len(cls.in_variables_channel.out_string) > 0 and cls.in_variables_channel.out_string != "null":
            string_vars = cls.in_variables_channel.out_string.split("&")
            for i in string_vars:
                name, value = i.split(";")
                curr_var = [x for x in ShufflecadHolder.variables_array if x.name == name][0]
                curr_var.value = value

    @classmethod
    def on_chart_vars(cls):
        only_charts = [i for i in ShufflecadHolder.variables_array if i.type_ == ShuffleVariable.CHART_TYPE]
        if len(only_charts) > 0:
            strings = ["{0};{1}".format(i.name, i.value) for i in only_charts]
            cls.chart_variables_channel.out_string = "&".join(strings)
        else:
            cls.chart_variables_channel.out_string = "null"

    @classmethod
    def on_outcad_vars(cls):
        if len(ShufflecadHolder.get_print_array()) > 0:
            to_print: str = "&".join(ShufflecadHolder.get_print_array())
            cls.outcad_variables_channel.out_string = to_print
            ShufflecadHolder.clear_print_array()
        else:
            cls.outcad_variables_channel.out_string = "null"

    @classmethod
    def on_rpi_vars(cls):
        out_lst = [Common.temperature, Common.memory_load,
                   Common.cpu_load, Common.power, Common.spi_time_dev,
                   Common.rx_spi_time_dev, Common.tx_spi_time_dev,
                   Common.spi_count_dev, Common.com_time_dev,
                   Common.rx_com_time_dev, Common.tx_com_time_dev,
                   Common.com_count_dev]
        cls.rpi_variables_channel.out_string = "&".join(map(str, out_lst))

    __camera_toggler = 0

    @classmethod
    def on_camera_vars(cls):
        # Logger.write_main_log(str(len(Shared.InfoHolder.camera_variables_array)))
        if len(ShufflecadHolder.camera_variables_array) > 0:
            if int(cls.camera_variables_channel.str_from_client) == -1:
                curr_var = ShufflecadHolder.camera_variables_array[cls.__camera_toggler]
                to_send_first = "{0};{1}".format(curr_var.name, ":".join(map(str, curr_var.shape)))
                # Logger.write_main_log(to_send_first)

                cls.camera_variables_channel.out_string = to_send_first
                cls.camera_variables_channel.out_bytes = curr_var.get_value()

                # Logger.write_main_log("sent")

                if cls.__camera_toggler + 1 == len(ShufflecadHolder.camera_variables_array):
                    cls.__camera_toggler = 0
                else:
                    cls.__camera_toggler += 1
            else:
                curr_var = ShufflecadHolder.camera_variables_array[int(cls.camera_variables_channel.str_from_client)]
                to_send_first = "{0};{1}".format(curr_var.name, ":".join(map(str, curr_var.shape)))

                cls.camera_variables_channel.out_string = to_send_first
                cls.camera_variables_channel.out_bytes = curr_var.get_value()
        else:
            cls.camera_variables_channel.out_string = "null"
            cls.camera_variables_channel.out_bytes = b'null'

    @classmethod
    def on_joy_vars(cls):
        if len(cls.joy_variables_channel.out_string) > 0 and cls.joy_variables_channel.out_string != "null":
            string_vars = cls.joy_variables_channel.out_string.split("&")
            for i in string_vars:
                name, value = i.split(";")
                ShufflecadHolder.joystick_values[name] = int(value)


class SplitFrames(object):
    def __init__(self, connection):
        self.connection = connection
        self.stream = io.BytesIO()
        self.count = 0
        self.name = ""

    def write_camera(self, buf, name):
        if buf.startswith(b'\xff\xd8'):
            # Start of new frame; send the old one's length
            # then the data
            size = self.stream.tell()
            if size > 0:
                nm = self.name.encode("utf-8")
                self.connection.write(struct.pack('<L', len(nm)))
                self.connection.flush()
                self.connection.write(nm)
                self.connection.flush()
                self.connection.write(struct.pack('<L', size))
                self.connection.flush()
                self.stream.seek(0)
                self.connection.write(self.stream.read(size))
                self.count += 1
                self.stream.seek(0)
                self.connection.flush()
        self.stream.write(buf)
        self.name = name

    def write(self, buf):
        self.connection.write(struct.pack('<L', len(buf)))
        self.connection.flush()
        self.connection.write(buf)
        self.count += 1
        self.connection.flush()

    def read(self) -> bytearray:
        data_len = struct.unpack('<L', self.connection.read(struct.calcsize('<L')))[0]
        return self.connection.read(data_len)
