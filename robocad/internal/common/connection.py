import socket
import threading
import time
import warnings
import struct

from .robot import Robot


class ListenPort:
    def __init__(self, robot: Robot, port: int):
        self.__port = port
        self.__robot = robot

        # other
        self.__stop_thread = False
        self.out_bytes = b''

        self.__sct = None
        self.__thread = None

    def start_listening(self):
        self.__thread = threading.Thread(target=self.listening, args=())
        self.__thread.start()

    def listening(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            self.__sct.connect(('127.0.0.1', self.__port))
        except ConnectionRefusedError:
            self.__robot.write_log("LP: Failed to connect on port " + str(self.__port))
            print("LP: Failed to connect on port " + str(self.__port))
        self.__robot.write_log("connected: " + str(self.__port))
        while not self.__stop_thread:
            try:
                dt = "Wait for data".encode('utf-16-le')
                dt_ln = struct.pack('<I', len(dt))
                self.__sct.sendall(dt_ln)
                self.__sct.sendall(dt)

                data_size = self.__sct.recv(4)
                if len(data_size) < 4:
                    continue
                length = (data_size[3] & 0xff) << 24 | (data_size[2] & 0xff) << 16 | \
                            (data_size[1] & 0xff) << 8 | (data_size[0] & 0xff)
                self.out_bytes = self.__sct.recv(length)
                # задержка для слабых компов
                time.sleep(0.004)
            except (ConnectionAbortedError, BrokenPipeError, OSError):
                # возникает при отключении сокета
                break
        self.__robot.write_log("disconnected: " + str(self.__port))
        try:
            self.__sct.shutdown(socket.SHUT_RDWR)
            self.__sct.close()
        except (OSError, Exception): pass  # idc

    def reset_out(self):
        self.out_bytes = b''

    def stop_listening(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception):
                self.__robot.write_log("Something went wrong while shutting down socket on port " +
                                                 str(self.__port))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем 1 секунды и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 1:
                        self.__robot.write_log("Something went wrong. Rude disconnection on port " +
                                                         str(self.__port))
                        try:
                            self.__sct.close()
                        except (OSError, Exception):
                            self.__robot.write_log("Something went wrong while closing socket on port " +
                                                             str(self.__port))
                        st_time = time.time()


class TalkPort:
    def __init__(self, robot: Robot, port: int):
        self.__port = port
        self.__robot = robot

        # other
        self.__stop_thread = False
        self.out_bytes = b''

        self.__sct = None
        self.__thread = None

    def start_talking(self):
        self.__thread = threading.Thread(target=self.talking, args=())
        self.__thread.start()

    def talking(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            self.__sct.connect(('127.0.0.1', self.__port))
        except ConnectionRefusedError:
            self.__robot.write_log("TP: Failed to connect on port " + str(self.__port))
            print("TP: Failed to connect on port " + str(self.__port))
        self.__robot.write_log("connected: " + str(self.__port))
        while not self.__stop_thread:
            try:
                dt_ln = struct.pack('<I', len(self.out_bytes))
                self.__sct.sendall(dt_ln)
                self.__sct.sendall(self.out_bytes)
                _ = self.__sct.recv(4)  # ответ сервера
                _ = self.__sct.recv(4)  # ответ сервера
                # задержка для слабых компов
                time.sleep(0.004)
            except (ConnectionAbortedError, BrokenPipeError, OSError):
                # возникает при отключении сокета
                break
        self.__robot.write_log("disconnected: " + str(self.__port))
        try:
            self.__sct.shutdown(socket.SHUT_RDWR)
            self.__sct.close()
        except (OSError, Exception): pass  # idc

    def reset_out(self):
        self.out_bytes = b''

    def stop_talking(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception):
                self.__robot.write_log("Something went wrong while shutting down socket on port " +
                                                 str(self.__port))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем 1 секунды и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 1:
                        self.__robot.write_log("Something went wrong. Rude disconnection on port " +
                                                         str(self.__port))
                        try:
                            self.__sct.close()
                        except (OSError, Exception):
                            self.__robot.write_log("Something went wrong while closing socket on port " +
                                                             str(self.__port))
                        st_time = time.time()
