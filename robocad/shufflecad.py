from typing import List
import cv2
import numpy as np
import signal
import io
import struct
from threading import Thread
import socket
import time
import os
import sys

from .internal.common.robot import Robot


class Shufflecad:
    def __init__(self, robot: Robot):
        self.__robot = robot
        self.variables_array: List[ShuffleVariable] = list()
        self.camera_variables_array: List[CameraVariable] = list()
        self.joystick_values: dict = dict()
        self.print_array: List[str] = list()

        signal.signal(signal.SIGTERM, self.__handler)
        signal.signal(signal.SIGINT, self.__handler)

        self.__connection_helper = ConnectionHelper(self, self.__robot)

    def stop(self):
        self.__connection_helper.stop()

    def add_var(self, var):
        if type(var) == CameraVariable:
            self.camera_variables_array.append(var)
        else:
            self.variables_array.append(var)
        return var
    
    def __handler(self, signum, _):
        self.__robot.write_log("Program stopped")
        self.__robot.write_log('Signal handler called with signal' + str(signum))
        self.__connection_helper.stop()
        raise SystemExit("Exited")
    
    # outcad methods
    def print_to_log(self, var: str, color: str = "#сссссс") -> None:
        self.print_array.append(var + color)

    def get_print_array(self) -> List[str]:
        return self.print_array

    def clear_print_array(self) -> None:
        self.print_array = list()

class ShuffleVariable(object):
    FLOAT_TYPE: str = "float"
    STRING_TYPE: str = "string"
    BIG_STRING_TYPE: str = "bigstring"
    BOOL_TYPE: str = "bool"
    CHART_TYPE: str = "chart"
    SLIDER_TYPE: str = "slider"
    RADAR_TYPE: str = "radar"

    IN_VAR: str = "in"
    OUT_VAR: str = "out"

    def __init__(self, name: str, type_: str, direction: str = IN_VAR) -> None:
        self.name = name
        self.type_ = type_
        self.value = ''
        self.direction = direction

    def set_bool(self, value: bool) -> None:
        self.value = "1" if value else "0"

    def set_float(self, value: float) -> None:
        self.value = str(value)

    def set_string(self, value: str) -> None:
        self.value = value

    def set_radar(self, value: list) -> None:
        complete_list = list()
        for i in value:
            complete_list.append(i['angle'])
            complete_list.append(i['value'])
        self.value = "+".join(map(str, complete_list))

    def get_bool(self) -> bool:
        return self.value == "1"

    def get_float(self) -> float:
        try:
            return float(self.value.replace(',', '.') if len(self.value) > 0 else "0")
        except (Exception, FloatingPointError):
            return 0

    def get_string(self) -> str:
        return self.value

class CameraVariable(object):
    def __init__(self, name: str) -> None:
        self.name = name
        self.value: np.ndarray = np.zeros((1, 1, 3), dtype=np.uint8)
        self.shape: tuple = (0, 0)

    def get_value(self) -> bytes:
        _, jpg = cv2.imencode('.jpg', self.value)
        return jpg

    def set_mat(self, mat) -> None:
        if mat is not None:
            self.shape = (mat.shape[1], mat.shape[0])
            self.value = mat

class ConnectionHelper:
    def __init__(self, shufflecad: Shufflecad, robot: Robot):
        self.__shufflecad = shufflecad
        self.__robot = robot
        self.out_variables_channel: TalkPort = TalkPort(self.__robot, 63253, self.on_out_vars, 0.004)
        self.in_variables_channel: ListenPort = ListenPort(self.__robot, 63258, self.on_in_vars, 0.004)
        self.chart_variables_channel: TalkPort = TalkPort(self.__robot, 63255, self.on_chart_vars, 0.002)
        self.outcad_variables_channel: TalkPort = TalkPort(self.__robot, 63257, self.on_outcad_vars, 0.1)
        self.rpi_variables_channel: TalkPort = TalkPort(self.__robot, 63256, self.on_rpi_vars, 0.5)
        self.camera_variables_channel: TalkPort = TalkPort(self.__robot, 63254, self.on_camera_vars, 0.03, True)
        self.joy_variables_channel: ListenPort = ListenPort(self.__robot, 63259, self.on_joy_vars, 0.004)
        self.start()

    def start(self):
        self.out_variables_channel.start_talking()
        self.in_variables_channel.start_listening()
        self.chart_variables_channel.start_talking()
        self.outcad_variables_channel.start_talking()
        self.rpi_variables_channel.start_talking()
        self.camera_variables_channel.start_talking()
        self.joy_variables_channel.start_listening()

    def stop(self):
        self.out_variables_channel.stop_talking()
        self.in_variables_channel.stop_listening()
        self.chart_variables_channel.stop_talking()
        self.outcad_variables_channel.stop_talking()
        self.rpi_variables_channel.stop_talking()
        self.camera_variables_channel.stop_talking()
        self.joy_variables_channel.stop_listening()

    def on_out_vars(self):
        without_charts = [i for i in self.__shufflecad.variables_array if i.type_ != ShuffleVariable.CHART_TYPE]
        if len(without_charts) > 0:
            strings = ["{0};{1};{2};{3}".format(i.name, i.value, i.type_, i.direction) for i in without_charts]
            self.out_variables_channel.out_string = "&".join(strings)
        else:
            self.out_variables_channel.out_string = "null"

    def on_in_vars(self):
        if len(self.in_variables_channel.out_string) > 0 and self.in_variables_channel.out_string != "null":
            string_vars = self.in_variables_channel.out_string.split("&")
            for i in string_vars:
                name, value = i.split(";")
                curr_var = [x for x in self.__shufflecad.variables_array if x.name == name][0]
                curr_var.value = value

    def on_chart_vars(self):
        only_charts = [i for i in self.__shufflecad.variables_array if i.type_ == ShuffleVariable.CHART_TYPE]
        if len(only_charts) > 0:
            strings = ["{0};{1}".format(i.name, i.value) for i in only_charts]
            self.chart_variables_channel.out_string = "&".join(strings)
        else:
            self.chart_variables_channel.out_string = "null"

    def on_outcad_vars(self):
        if len(self.__shufflecad.get_print_array()) > 0:
            to_print: str = "&".join(self.__shufflecad.get_print_array())
            self.outcad_variables_channel.out_string = to_print
            self.__shufflecad.clear_print_array()
        else:
            self.outcad_variables_channel.out_string = "null"

    def on_rpi_vars(self):
        out_lst = [self.__robot.robot_info.temperature, self.__robot.robot_info.memory_load,
                   self.__robot.robot_info.cpu_load, self.__robot.power, self.__robot.robot_info.spi_time_dev,
                   self.__robot.robot_info.rx_spi_time_dev, self.__robot.robot_info.tx_spi_time_dev,
                   self.__robot.robot_info.spi_count_dev, self.__robot.robot_info.com_time_dev,
                   self.__robot.robot_info.rx_com_time_dev, self.__robot.robot_info.tx_com_time_dev,
                   self.__robot.robot_info.com_count_dev]
        self.rpi_variables_channel.out_string = "&".join(map(str, out_lst))

    __camera_toggler = 0

    def on_camera_vars(self):
        # Logger.write_main_log(str(len(Shared.InfoHolder.camera_variables_array)))
        if len(self.__shufflecad.camera_variables_array) > 0:
            if int(self.camera_variables_channel.str_from_client) == -1:
                curr_var = self.__shufflecad.camera_variables_array[self.__camera_toggler]
                to_send_first = "{0};{1}".format(curr_var.name, ":".join(map(str, curr_var.shape)))
                # Logger.write_main_log(to_send_first)

                self.camera_variables_channel.out_string = to_send_first
                self.camera_variables_channel.out_bytes = curr_var.get_value()

                # Logger.write_main_log("sent")

                if self.__camera_toggler + 1 == len(self.__shufflecad.camera_variables_array):
                    self.__camera_toggler = 0
                else:
                    self.__camera_toggler += 1
            else:
                curr_var = self.__shufflecad.camera_variables_array[int(self.camera_variables_channel.str_from_client)]
                to_send_first = "{0};{1}".format(curr_var.name, ":".join(map(str, curr_var.shape)))

                self.camera_variables_channel.out_string = to_send_first
                self.camera_variables_channel.out_bytes = curr_var.get_value()
        else:
            self.camera_variables_channel.out_string = "null"
            self.camera_variables_channel.out_bytes = b'null'

    def on_joy_vars(self):
        if len(self.joy_variables_channel.out_string) > 0 and self.joy_variables_channel.out_string != "null":
            string_vars = self.joy_variables_channel.out_string.split("&")
            for i in string_vars:
                name, value = i.split(";")
                self.__shufflecad.joystick_values[name] = int(value)

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
    
class ListenPort:
    def __init__(self, robot: Robot, port: int, event_handler=None, delay: float = 0.004):
        self.__port = port
        self.__robot = robot

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

        try:
            connection_out = self.__sct.accept()[0].makefile('rwb')
        except OSError:
            self.__robot.write_log("Shufflecad LP: Failed to connect on port " + str(self.__port))
            return
        
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
                self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                self.__robot.write_log(str(e))
                break
        try:
            self.__sct.shutdown(socket.SHUT_RDWR)
            self.__sct.close()
        except (OSError, Exception): pass  # idc

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
                self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                self.__robot.write_log(str(e))
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
                            self.__robot.write_log(" ".join(map(str,
                                                                          [exc_type, file_name, exc_tb.tb_lineno])))
                            self.__robot.write_log(str(e))
                        st_time = time.time()


class TalkPort:
    def __init__(self, robot: Robot, port: int, event_handler=None, delay: float = 0.004, is_camera: bool = False):
        self.__port = port
        self.__robot = robot

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

        try:
            connection_out = self.__sct.accept()[0].makefile('rwb')
        except OSError:
            self.__robot.write_log("Shufflecad TP: Failed to connect on port " + str(self.__port))
            return
        
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
                self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                self.__robot.write_log(str(e))
                break
        try:
            self.__sct.shutdown(socket.SHUT_RDWR)
            self.__sct.close()
        except (OSError, Exception): pass  # idc

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
                self.__robot.write_log(" ".join(map(str, [exc_type, file_name, exc_tb.tb_lineno])))
                self.__robot.write_log(str(e))
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
                            self.__robot.write_log(" ".join(map(str,
                                                                          [exc_type, file_name, exc_tb.tb_lineno])))
                            self.__robot.write_log(str(e))
                        st_time = time.time()

