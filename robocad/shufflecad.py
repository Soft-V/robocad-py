from typing import List
import cv2
import numpy as np
import signal
import io
import struct
import threading
from threading import Thread
import socket
import time
import os
import sys

from .internal.common.robot import Robot


class Shufflecad:
    LOG_INFO: str = "info"
    LOG_WARNING: str = "warning"
    LOG_ERROR: str = "error"

    def __init__(self, robot: Robot):
        self.__robot = robot
        self.variables_array: List[ShuffleVariable] = list()
        self.camera_variables_array: List[CameraVariable] = list()
        self.joystick_data: JoystickData = JoystickData()
        self.print_array: List[str] = list()

        if threading.current_thread() is threading.main_thread():
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
    def print_to_log(self, message: str, message_type: str = LOG_INFO, color: str = "#808080") -> None:
        self.print_array.append(message_type + "@" + message + color)

    def get_print_array(self) -> List[str]:
        return self.print_array

    def clear_print_array(self) -> None:
        self.print_array = list()

class JoystickData:
    def __init__(self):
        self.btn_a: bool = False
        self.btn_b: bool = False
        self.btn_x: bool = False
        self.btn_y: bool = False
        
        self.dpud_up: bool = False
        self.dpud_down: bool = False
        self.dpud_left: bool = False
        self.dpud_right: bool = False
        
        self.right_trigger: int = 0
        self.left_trigger: int = 0
        
        self.right_stick_x: int = 0
        self.right_stick_y: int = 0
        
        self.left_stick_x: int = 0
        self.left_stick_y: int = 0
        
        self.right_shoulder: bool = False
        self.left_shoulder: bool = False
    

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
        for i in range(len(value)):
            complete_list.append(i)
            complete_list.append(value[i])
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
    # Камеры: список (имя;ширина:высота) идёт по TCP, а кадры — по UDP чанками.
    CAMERA_UDP_PORT = 63260
    CAMERA_UDP_CHUNK = 1400

    def __init__(self, shufflecad: Shufflecad, robot: Robot):
        self.__shufflecad = shufflecad
        self.__robot = robot
        self.out_variables_channel: TalkPort = TalkPort(self.__robot, 63253, self.on_out_vars, 0.004)
        self.in_variables_channel: ListenPort = ListenPort(self.__robot, 63258, self.on_in_vars, 0.004)
        self.chart_variables_channel: TalkPort = TalkPort(self.__robot, 63255, self.on_chart_vars, 0.002)
        self.outcad_variables_channel: TalkPort = TalkPort(self.__robot, 63257, self.on_outcad_vars, 0.1)
        self.rpi_variables_channel: TalkPort = TalkPort(self.__robot, 63256, self.on_rpi_vars, 0.5)
        # Камера-канал теперь отдаёт только метаданные (список камер), без картинок.
        self.camera_variables_channel: TalkPort = TalkPort(self.__robot, 63254, self.on_camera_vars, 0.03)
        self.joy_variables_channel: ListenPort = ListenPort(self.__robot, 63259, self.on_joy_vars, 0.004)

        self.__selected_camera = 0
        self.__stop_camera_udp = False
        self.__camera_udp_sock = None
        self.__camera_udp_thread = None

        self.start()

    def start(self):
        self.out_variables_channel.start_talking()
        self.in_variables_channel.start_listening()
        self.chart_variables_channel.start_talking()
        self.outcad_variables_channel.start_talking()
        self.rpi_variables_channel.start_talking()
        self.camera_variables_channel.start_talking()
        self.joy_variables_channel.start_listening()
        self.start_camera_udp()

    def stop(self):
        self.out_variables_channel.stop_talking()
        self.in_variables_channel.stop_listening()
        self.chart_variables_channel.stop_talking()
        self.outcad_variables_channel.stop_talking()
        self.rpi_variables_channel.stop_talking()
        self.camera_variables_channel.stop_talking()
        self.joy_variables_channel.stop_listening()
        self.stop_camera_udp()

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
                found_by_name = [x for x in self.__shufflecad.variables_array if x.name == name]
                if len(found_by_name) == 0:
                    continue
                curr_var = found_by_name[0]
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

    def on_camera_vars(self):
        # Отдаём весь список камер каждый цикл — клиент всегда видит актуальный набор.
        cams = self.__shufflecad.camera_variables_array
        if len(cams) > 0:
            segs = ["{0};{1}".format(c.name, ":".join(map(str, c.shape))) for c in cams]
            self.camera_variables_channel.out_string = "&".join(segs)
        else:
            self.camera_variables_channel.out_string = "null"

        # Клиент присылает индекс выбранной камеры — её кадры уходят по UDP.
        try:
            self.__selected_camera = int(self.camera_variables_channel.str_from_client)
        except (ValueError, TypeError):
            pass

    def start_camera_udp(self):
        self.__stop_camera_udp = False
        self.__camera_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__camera_udp_thread = Thread(target=self.camera_udp_loop, args=(), daemon=True)
        self.__camera_udp_thread.start()

    def stop_camera_udp(self):
        self.__stop_camera_udp = True
        if self.__camera_udp_sock is not None:
            try:
                self.__camera_udp_sock.close()
            except (OSError, Exception):
                pass

    def camera_udp_loop(self):
        # Кадр выбранной камеры режем на чанки и шлём по UDP: заголовок
        # (frameId:u32, cameraIndex:u16, chunkIndex:u16, chunkCount:u16) + данные.
        frame_id = 0
        while not self.__stop_camera_udp:
            try:
                target = self.camera_variables_channel.client_address
                cams = self.__shufflecad.camera_variables_array
                if target is not None and len(cams) > 0:
                    idx = self.__selected_camera
                    if idx < 0 or idx >= len(cams):
                        idx = 0
                    cam = cams[idx]
                    if cam.shape[0] > 0 and cam.shape[1] > 0:
                        data = cam.get_value().tobytes()
                        # get_value возвращает JPEG (начинается с FF D8)
                        if len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8:
                            self.send_frame_udp(target, idx, data, frame_id)
                            frame_id = (frame_id + 1) & 0xFFFFFFFF
            except (OSError, Exception):
                pass
            time.sleep(0.03)

    def send_frame_udp(self, target: str, camera_index: int, data: bytes, frame_id: int):
        total = (len(data) + self.CAMERA_UDP_CHUNK - 1) // self.CAMERA_UDP_CHUNK
        if total < 1:
            total = 1
        for i in range(total):
            off = i * self.CAMERA_UDP_CHUNK
            chunk = data[off:off + self.CAMERA_UDP_CHUNK]
            header = struct.pack('<IHHH', frame_id, camera_index, i, total)
            try:
                self.__camera_udp_sock.sendto(header + chunk, (target, self.CAMERA_UDP_PORT))
            except (OSError, Exception):
                pass

    def on_joy_vars(self):
        if len(self.joy_variables_channel.out_string) > 0 and self.joy_variables_channel.out_string != "null":
            string_vars = self.joy_variables_channel.out_string.split("&")
            for i in string_vars:
                name, value = i.split(";")
                int_val = int(value)
                if (name == "A"):
                    self.__shufflecad.joystick_data.btn_a = int_val == 1
                elif (name == "X"):
                    self.__shufflecad.joystick_data.btn_x = int_val == 1
                elif (name == "Y"):
                    self.__shufflecad.joystick_data.btn_y = int_val == 1
                elif (name == "B"):
                    self.__shufflecad.joystick_data.btn_b = int_val == 1
                elif (name == "RightShoulder"):
                    self.__shufflecad.joystick_data.right_shoulder = int_val == 1
                elif (name == "LeftShoulder"):
                    self.__shufflecad.joystick_data.left_shoulder = int_val == 1
                elif (name == "DPad_Up"):
                    self.__shufflecad.joystick_data.dpud_up = int_val == 1
                elif (name == "DPad_Down"):
                    self.__shufflecad.joystick_data.dpud_down = int_val == 1
                elif (name == "DPad_Right"):
                    self.__shufflecad.joystick_data.dpud_right = int_val == 1
                elif (name == "DPad_Left"):
                    self.__shufflecad.joystick_data.dpud_left = int_val == 1
                elif (name == "LeftTrigger"):
                    self.__shufflecad.joystick_data.left_trigger = int_val
                elif (name == "RightTrigger"):
                    self.__shufflecad.joystick_data.right_trigger = int_val
                elif (name == "LeftThumbstick_X"):
                    self.__shufflecad.joystick_data.left_stick_x = int_val
                elif (name == "LeftThumbstick_Y"):
                    self.__shufflecad.joystick_data.left_stick_y = int_val
                elif (name == "RightThumbstick_X"):
                    self.__shufflecad.joystick_data.right_stick_x = int_val
                elif (name == "RightThumbstick_Y"):
                    self.__shufflecad.joystick_data.right_stick_y = int_val

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

        # IP клиента (shufflecad) — нужен, чтобы слать кадры камеры по UDP
        self.client_address = None

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
            conn, addr = self.__sct.accept()
            self.client_address = addr[0]
            connection_out = conn.makefile('rwb')
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

