from .shared import InfoHolder, CameraVariable
from .logger import Logger
from .connections import ConnectionHelper
import signal


class Shufflecad:
    @classmethod
    def start(cls):
        InfoHolder.logger = Logger()
        signal.signal(signal.SIGTERM, cls.handler)
        signal.signal(signal.SIGINT, cls.handler)
        ConnectionHelper.init_and_start()

    @classmethod
    def stop(cls):
        ConnectionHelper.stop()

    @classmethod
    def add_var(cls, var):
        if type(var) == CameraVariable:
            InfoHolder.camera_variables_array.append(var)
        else:
            InfoHolder.variables_array.append(var)
        return var

    @classmethod
    def handler(cls, signum, _):
        InfoHolder.logger.write_main_log("Program stopped")
        InfoHolder.logger.write_main_log('Signal handler called with signal' + str(signum))
        ConnectionHelper.stop()
        raise SystemExit("Exited")
