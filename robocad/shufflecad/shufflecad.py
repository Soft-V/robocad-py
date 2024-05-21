from typing import List

import cv2
import numpy as np
from .connections import ConnectionHelper
from .shufflecad_holder import CameraVariable, ShufflecadHolder
from robocad.common import Common
import signal


class Shufflecad:
    @classmethod
    def start(cls):
        signal.signal(signal.SIGTERM, cls.__handler)
        signal.signal(signal.SIGINT, cls.__handler)
        ConnectionHelper.init_and_start()

    @classmethod
    def stop(cls):
        ConnectionHelper.stop()

    @classmethod
    def add_var(cls, var):
        if type(var) == CameraVariable:
            ShufflecadHolder.camera_variables_array.append(var)
        else:
            ShufflecadHolder.variables_array.append(var)
        return var
    
    # outcad methods
    @classmethod
    def print_to_log(cls, var: str, color: str = "#e0d4ab") -> None:
        ShufflecadHolder.print_to_log(var + color)

    @classmethod
    def __handler(cls, signum, _):
        Common.logger.write_main_log("Program stopped")
        Common.logger.write_main_log('Signal handler called with signal' + str(signum))
        ConnectionHelper.stop()
        raise SystemExit("Exited")
