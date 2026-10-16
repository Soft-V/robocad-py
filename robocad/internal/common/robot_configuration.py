class LidarTypes:
    N10_LIDAR = 0
    YD_LIDAR_X2 = 1

class RobotConfiguration:
    def __init__(self):
        self.camera_index = 0
        self.lib_holder_first_path = '/home/pi'

        self.lidar_type = LidarTypes.N10_LIDAR
        self.lidar_port = '/dev/ttyUSB0'

        self.sim_log_path = './robocad.log'
        self.real_log_path = '/var/tmp/robocad.log'


class DefaultStudicaConfiguration(RobotConfiguration):
    def __init__(self):
        super().__init__()
        # pigpiod is started by the OS, not by the robot library.
        self.pigpio_pipe_path = '/dev/pigpio'
        self.pigpio_response_path = '/dev/pigout'
        self.pigpio_timeout = 1.0
        self.hcdio_pwm_frequency = 100
        self.titan_port = '/dev/ttyACM0'
        self.titan_baud = 115200
        self.vmx_port = "/dev/spidev1.2"
        self.vmx_ch = 2
        self.vmx_speed = 1000000
        self.vmx_mode = 0


class DefaultAlgaritmConfiguration(RobotConfiguration):
    def __init__(self):
        super().__init__()
        self.camera_index = 0

        self.titan_port = '/dev/ttyACM0'
        self.titan_baud = 115200
        self.vmx_port = "/dev/spidev0.0"
        self.vmx_ch = 0
        self.vmx_speed = 1000000
        self.vmx_mode = 0

class DefaultCommonConfiguration(RobotConfiguration):
    def __init__(self):
        super().__init__()
