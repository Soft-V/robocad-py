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


class InfoHolder:
    # logger object
    logger = None
    # control the type of the shufflecad work
    on_real_robot: bool = True

    power: str = "0"

    # some things
    spi_time_dev: str = "0"
    rx_spi_time_dev: str = "0"
    tx_spi_time_dev: str = "0"
    spi_count_dev: str = "0"
    com_time_dev: str = "0"
    rx_com_time_dev: str = "0"
    tx_com_time_dev: str = "0"
    com_count_dev: str = "0"
    temperature: str = "0"
    memory_load: str = "0"
    cpu_load: str = "0"

    variables_array: List[ShuffleVariable] = list()
    camera_variables_array: List[CameraVariable] = list()
    joystick_values: dict = dict()
    print_array: List[str] = list()

    # outcad methods
    @classmethod
    def print_to_log(cls, var: str, color: str = "#e0d4ab") -> None:
        cls.print_array.append(var + color)

    @classmethod
    def get_print_array(cls) -> List[str]:
        return cls.print_array

    @classmethod
    def clear_print_array(cls) -> None:
        cls.print_array = list()
