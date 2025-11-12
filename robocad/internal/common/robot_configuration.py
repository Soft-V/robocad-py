class RobotConfiguration:
    def __init__(self):
        self.camera_index = 0
        self.lib_holder_first_path = '/home/pi'
        self.with_pi_blaster = True
        self.lidar_port = '/dev/ttyUSB0'

        self.sim_log_path = './robocad.log'
        self.real_log_path = '/var/tmp/robocad.log'


class DefaultStudicaConfiguration(RobotConfiguration):
    def __init__(self):
        super().__init__()
        self.titan_port = '/dev/ttyACM0'
        self.titan_baud = 115200
        self.vmx_port = "/dev/spidev1.2"
        self.vmx_ch = 2
        self.vmx_speed = 1000000
        self.vmx_mode = 0


class DefaultAlgaritmConfiguration(RobotConfiguration):
    def __init__(self):
        super().__init__()
        self.camera_index = 2
        self.with_pi_blaster = False

        self.titan_port = '/dev/ttyACM0'
        self.titan_baud = 115200
        self.vmx_port = "/dev/spidev0.0"
        self.vmx_ch = 0
        self.vmx_speed = 1000000
        self.vmx_mode = 0
