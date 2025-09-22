import ctypes


class LibHolder:
    def __init__(self):
        self.lib = ctypes.cdll.LoadLibrary('/home/pi/CommonRPiLibrary/CommonRPiLibrary/build/libCommonRPiLibrary.so')
        self.lib.StartSPI.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.StartUSB.argtypes = [ctypes.c_char_p, ctypes.c_int]

    def init_spi(self, path: str, channel: int, speed: int, mode: int):
        c_path = path.encode('utf-8') 
        self.lib.StartSPI(c_path, channel, speed, mode)
        self.lib.ReadWriteSPI.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint]
        self.lib.ReadWriteSPI.restype = ctypes.POINTER(ctypes.c_ubyte)

    def init_usb(self, path: str, baud: int):
        c_path = path.encode('utf-8') 
        self.lib.StartUSB(c_path, baud)
        self.lib.ReadWriteUSB.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint]
        self.lib.ReadWriteUSB.restype = ctypes.POINTER(ctypes.c_ubyte)

    def rw_spi(self, array: bytearray) -> bytearray:
        data_array = (ctypes.c_ubyte * len(array))(*array)
        data_length = len(array)
        returned_array_ptr = self.lib.ReadWriteSPI(data_array, data_length)
        return bytearray([returned_array_ptr[i] for i in range(data_length)])

    def rw_usb(self, array: bytearray) -> bytearray:
        data_array = (ctypes.c_ubyte * len(array))(*array)
        data_length = len(array)
        returned_array_ptr = self.lib.ReadWriteUSB(data_array, data_length)
        return bytearray([returned_array_ptr[i] for i in range(data_length)])

    def stop_spi(self):
        self.lib.StopSPI()

    def stop_usb(self):
        self.lib.StopUSB()
