from abc import ABC, abstractmethod


class ConnectionBase(ABC):
    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_camera(self):
        pass
