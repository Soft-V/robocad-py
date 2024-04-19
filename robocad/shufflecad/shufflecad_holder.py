
from typing import List

import cv2
import numpy as np


class ShuffleVariable(object):
    FLOAT_TYPE: str = "float"
    STRING_TYPE: str = "string"
    BIG_STRING_TYPE: str = "bigstring"
    BOOL_TYPE: str = "bool"
    CHART_TYPE: str = "chart"
    SLIDER_TYPE: str = "slider"

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


class ShufflecadHolder:
    variables_array: List[ShuffleVariable] = list()
    camera_variables_array: List[CameraVariable] = list()
    joystick_values: dict = dict()
    print_array: List[str] = list()

    # outcad methods
    @classmethod
    def print_to_log(cls, var: str) -> None:
        ShufflecadHolder.print_array.append(var)

    @classmethod
    def get_print_array(cls) -> List[str]:
        return ShufflecadHolder.print_array

    @classmethod
    def clear_print_array(cls) -> None:
        ShufflecadHolder.print_array = list()