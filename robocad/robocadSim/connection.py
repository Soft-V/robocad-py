import socket
import threading
import time
import warnings

from shufflecad.shared import InfoHolder


class ListenPort:
    def __init__(self, port: int, is_camera=False):
        self.__port = port
        self.__is_camera = is_camera

        # other
        self.__stop_thread = False
        self.out_string = ''
        self.out_bytes = b''

        self.__sct = None
        self.__thread = None

    def start_listening(self):
        self.__thread = threading.Thread(target=self.listening, args=())
        self.__thread.start()

    def listening(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.__sct.connect(('127.0.0.1', self.__port))
        InfoHolder.logger.write_main_log("connected: " + str(self.__port))
        while not self.__stop_thread:
            try:
                if self.__is_camera:
                    self.__sct.sendall("Wait for size".encode('utf-16-le'))
                    image_size = self.__sct.recv(4)
                    if len(image_size) < 4:
                        continue
                    buffer_size = (image_size[3] & 0xff) << 24 | (image_size[2] & 0xff) << 16 | \
                                  (image_size[1] & 0xff) << 8 | (image_size[0] & 0xff)
                    self.__sct.sendall("Wait for image".encode('utf-16-le'))
                    self.out_bytes = self.__sct.recv(buffer_size)
                else:
                    self.__sct.sendall("Wait for data".encode('utf-16-le'))
                    data_size = self.__sct.recv(4)
                    if len(data_size) < 4:
                        continue
                    length = (data_size[3] & 0xff) << 24 | (data_size[2] & 0xff) << 16 | \
                             (data_size[1] & 0xff) << 8 | (data_size[0] & 0xff)
                    self.out_bytes = self.__sct.recv(length)
                    self.out_string = self.out_bytes.decode('utf-16-le')
                # задержка для слабых компов
                time.sleep(0.004)
            except (ConnectionAbortedError, BrokenPipeError):
                # возникает при отключении сокета
                break
        InfoHolder.logger.write_main_log("disconnected: " + str(self.__port))
        self.__sct.shutdown(socket.SHUT_RDWR)
        self.__sct.close()

    def reset_out(self):
        self.out_string = ''
        self.out_bytes = b''

    def stop_listening(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception):
                InfoHolder.logger.write_main_log("Something went wrong while shutting down socket on port " +
                                                 str(self.__port))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем 1 секунды и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 1:
                        InfoHolder.logger.write_main_log("Something went wrong. Rude disconnection on port " +
                                                         str(self.__port))
                        try:
                            self.__sct.close()
                        except (OSError, Exception):
                            InfoHolder.logger.write_main_log("Something went wrong while closing socket on port " +
                                                             str(self.__port))
                        st_time = time.time()


class TalkPort:
    def __init__(self, port: int):
        self.__port = port

        # other
        self.__stop_thread = False
        self.out_string = ''

        self.__sct = None
        self.__thread = None

    def start_talking(self):
        self.__thread = threading.Thread(target=self.talking, args=())
        self.__thread.start()

    def talking(self):
        self.__sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.__sct.connect(('127.0.0.1', self.__port))
        InfoHolder.logger.write_main_log("connected: " + str(self.__port))
        while not self.__stop_thread:
            try:
                self.__sct.sendall((self.out_string + "$").encode('utf-16-le'))
                _ = self.__sct.recv(1024)  # ответ сервера
                # задержка для слабых компов
                time.sleep(0.004)
            except (ConnectionAbortedError, BrokenPipeError):
                # возникает при отключении сокета
                break
        InfoHolder.logger.write_main_log("disconnected: " + str(self.__port))
        self.__sct.shutdown(socket.SHUT_RDWR)
        self.__sct.close()

    def reset_out(self):
        self.out_string = ''

    def stop_talking(self):
        self.__stop_thread = True
        self.reset_out()
        if self.__sct is not None:
            try:
                self.__sct.shutdown(socket.SHUT_RDWR)
            except (OSError, Exception):
                InfoHolder.logger.write_main_log("Something went wrong while shutting down socket on port " +
                                                 str(self.__port))
            if self.__thread is not None:
                st_time = time.time()
                # если поток все еще живой, ждем 1 секунды и закрываем сокет
                while self.__thread.is_alive():
                    if time.time() - st_time > 1:
                        InfoHolder.logger.write_main_log("Something went wrong. Rude disconnection on port " +
                                                         str(self.__port))
                        try:
                            self.__sct.close()
                        except (OSError, Exception):
                            InfoHolder.logger.write_main_log("Something went wrong while closing socket on port " +
                                                             str(self.__port))
                        st_time = time.time()


class ParseChannels:
    @staticmethod
    def parse_float_channel(txt: str):
        try:
            return tuple(map(float, txt.replace(',', '.').split(';')))
        except (Exception, ValueError):
            return tuple()

    @staticmethod
    def parse_bool_channel(txt: str):
        try:
            return tuple(map(bool, map(int, txt.split(';'))))
        except (Exception, ValueError):
            return tuple()

    @staticmethod
    def join_float_channel(lst: tuple):
        return ';'.join(map(str, lst))

    @staticmethod
    def join_bool_channel(lst: tuple):
        return ';'.join(map(str, map(int, lst)))
