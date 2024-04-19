import sys
import ctypes
from robocad.common import Common


class LibHolder:
    lib = None

    @classmethod
    def init(cls):
        if cls.lib is None:
            cls.lib = ctypes.cdll.LoadLibrary('/home/pi/CommonRPiLibrary/CommonRPiLibrary/build/libCommonRPiLibrary.so')

    @classmethod
    def init_spi(cls):
        if cls.lib is not None:
            cls.lib.StartSPI()
            cls.lib.ReadWriteSPI.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint]
            cls.lib.ReadWriteSPI.restype = ctypes.POINTER(ctypes.c_ubyte)

    @classmethod
    def init_usb(cls):
        if cls.lib is not None:
            cls.lib.StartUSB()
            cls.lib.ReadWriteUSB.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint]
            cls.lib.ReadWriteUSB.restype = ctypes.POINTER(ctypes.c_ubyte)

    @classmethod
    def rw_spi(cls, array: bytearray) -> bytearray:
        data_array = (ctypes.c_ubyte * len(array))(*array)
        data_length = len(array)
        returned_array_ptr = cls.lib.ReadWriteSPI(data_array, data_length)
        return bytearray([returned_array_ptr[i] for i in range(data_length)])

    @classmethod
    def rw_usb(cls, array: bytearray) -> bytearray:
        data_array = (ctypes.c_ubyte * len(array))(*array)
        data_length = len(array)
        returned_array_ptr = cls.lib.ReadWriteUSB(data_array, data_length)
        return bytearray([returned_array_ptr[i] for i in range(data_length)])

    @classmethod
    def stop_spi(cls):
        if cls.lib is not None:
            cls.lib.StopSPI()

    @classmethod
    def stop_usb(cls):
        if cls.lib is not None:
            cls.lib.StopUSB()


class TitanStatic:
    # from Titan
    speed_motor_0: float = 0.0
    speed_motor_1: float = 0.0
    speed_motor_2: float = 0.0
    speed_motor_3: float = 0.0

    enc_motor_0: int = 0
    enc_motor_1: int = 0
    enc_motor_2: int = 0
    enc_motor_3: int = 0

    raw_enc_motor_0: int = 0
    raw_enc_motor_1: int = 0
    raw_enc_motor_2: int = 0
    raw_enc_motor_3: int = 0

    limit_l_0: bool = False
    limit_h_0: bool = False
    limit_l_1: bool = False
    limit_h_1: bool = False
    limit_l_2: bool = False
    limit_h_2: bool = False
    limit_l_3: bool = False
    limit_h_3: bool = False


class VMXStatic:
    HCDIO_CONST_ARRAY = [4, 18, 17, 27, 23, 22, 24, 25, 7, 5]

    yaw: float = 0
    yaw_unlim: float = 0
    calib_imu: bool = False

    ultrasound_1: float = 0
    ultrasound_2: float = 0

    analog_1: int = 0
    analog_2: int = 0
    analog_3: int = 0
    analog_4: int = 0

    flex_0: bool = False
    flex_1: bool = False
    flex_2: bool = False
    flex_3: bool = False
    flex_4: bool = False
    flex_5: bool = False
    flex_6: bool = False
    flex_7: bool = False

    hcdio_values: list[float] = [0.0] * 10

    @classmethod
    def set_servo_angle(cls, angle: float, pin: int):
        dut: float = 0.000666 * angle + 0.05
        cls.hcdio_values[pin] = dut
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def set_led_state(cls, state: bool, pin: int):
        dut: float = 0.2 if state else 0.0
        cls.hcdio_values[pin] = dut
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def set_servo_pwm(cls, pwm: float, pin: int):
        dut: float = pwm
        cls.hcdio_values[pin] = dut
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def disable_servo(cls, pin: int):
        cls.hcdio_values[pin] = 0.0
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + "0.0")

    @staticmethod
    def echo_to_file(st: str):
        if not Common.on_real_robot:
            return None
        original_stdout = sys.stdout
        with open('/dev/pi-blaster', 'w') as f:
            sys.stdout = f  # Change the standard output to the file we created.
            print(st)
            sys.stdout = original_stdout  # Reset the standard output to its original value
