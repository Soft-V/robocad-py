from abc import ABC, abstractmethod


class LidarBase(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def get_data(self) -> list[int]:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
