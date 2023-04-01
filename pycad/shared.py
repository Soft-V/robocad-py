import sys


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

    @classmethod
    def set_servo_angle(cls, angle: float, pin: int):
        dut: float = 0.000666 * angle + 0.05
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def set_led_state(cls, state: bool, pin: int):
        dut: float = 0.2 if state else 0.0
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def set_servo_pwm(cls, pwm: float, pin: int):
        dut: float = pwm
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + str(dut))

    @classmethod
    def disable_servo(cls, pin: int):
        VMXStatic.echo_to_file(str(cls.HCDIO_CONST_ARRAY[pin]) + "=" + "0.0")

    @staticmethod
    def echo_to_file(st: str):
        original_stdout = sys.stdout
        with open('/dev/pi-blaster', 'w') as f:
            sys.stdout = f  # Change the standard output to the file we created.
            print(st)
            sys.stdout = original_stdout  # Reset the standard output to its original value
