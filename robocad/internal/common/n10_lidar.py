from serial import Serial
from typing import Callable
import threading

from .robot import Robot
from .lidar import LidarBase

class N10Lidar(LidarBase):
    MAX_BUF = 230400
    PKG_HEADER_0 = 0xA5
    PKG_HEADER_1 = 0x5A
    MIN_PAYLOAD = 58
    POINT_PER_PACK = 16

    def __init__(self, robot: Robot, port, baud=230400):
        self.__robot = robot
        self.serial = Serial(port, baud)
        self._shutdown = False

        self._data = [0] * 360
    
    def get_raw(self):
        while self.serial.in_waiting < N10Lidar.MIN_PAYLOAD:
            pass
        return self.serial.read(self.serial.in_waiting)
    
    def _scan(self):
        data = []
        while not self._shutdown:
            [data.append(i) for i in self.get_raw()]

            if len(data) < N10Lidar.MIN_PAYLOAD:
                continue

            if len(data) > N10Lidar.MIN_PAYLOAD * 100:
                data = []

            start = 0
            while start < len(data)-2:
                start = 0
                while start < len(data)-2:
                    if data[start] == N10Lidar.PKG_HEADER_0 and data[start+1] == N10Lidar.PKG_HEADER_1:
                        break
                    start += 1

                _data = data[start:start+N10Lidar.MIN_PAYLOAD]

                if len(_data) < N10Lidar.MIN_PAYLOAD:
                    break

                start_angle = (_data[5] * 256 + _data[6])
                end_angle = (_data[55] * 256 + _data[56])

                final_data = []
                diff = ((end_angle + 36000 - start_angle) % 36000) / (N10Lidar.POINT_PER_PACK - 1) / 100
                _start_angle = start_angle / 100

                for i in range(N10Lidar.POINT_PER_PACK):
                    o = 7+(i*3)
                    final_data.append(( round(_start_angle + diff * i) % 360 , (
                        (_data[o] * 256) + 
                        _data[o+1]) 
                    ))
                
                data = data[N10Lidar.MIN_PAYLOAD:]

                self.__handle_data(final_data)
    
    def __handle_data(self, data):
        for i in data:
            self._data[i[0]] = i[1]

    def stop(self):
        self.shutdown()
        
    def start(self):
        self._scan_thread = threading.Thread(target = self._scan)
        self._scan_thread.start()

    def get_data(self):
        return self._data

    def shutdown(self):
        self._shutdown = True

if __name__ == '__main__':
    n10 = N10Lidar('COM7')
    n10.scan(lambda x:[print(i[0], i[1]) for i in x])
