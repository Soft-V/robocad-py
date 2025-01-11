from abc import ABC, abstractmethod

import cv2


class ConnectionBase(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_camera(self):
        pass
