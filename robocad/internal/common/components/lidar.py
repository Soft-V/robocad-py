import serial
import struct
import time
import math
import csv
import binascii
import numpy as np

class YDLidarX2:
    def __init__(self, port, baudrate=115200, timeout=1.0):
        """
        port: e.g. '/dev/ttyUSB0' or 'COM3'
        baudrate: usually 115200.
        """
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.buf = bytearray()

        if self.ser is None or (not self.ser.is_open):
            raise Exception("Failed to open serial on port " + str(port))

    def close(self):
        self.ser.close()

    def _read_to_buffer(self, n=1):
        data = self.ser.read(n)
        if data:
            self.buf.extend(data)
        return data

    def _find_header(self):
        # В мануале PH == 0x55AA (low first) — ищем байтовую последовательность 0x55 0xAA
        # (мануал содержит также примеры с A5 5A — если потребуется, добавьте поиск)
        sig = b'\xaa\x55'
        idx = self.buf.find(sig)
        return idx

    def _pop_bytes(self, n):
        out = self.buf[:n]
        del self.buf[:n]
        return bytes(out)

    def read_scan_packet(self, wait_timeout=2.0):
        """
        Читает следующий полный пакет сканирования и возвращает список точек (angles_deg, dist_mm).
        Возвращает None если не удалось в пределах таймаута.
        """
        start_time = time.time()
        while True:
            # наполняем буфер
            self._read_to_buffer(512)
            idx = self._find_header()
            if idx >= 0:
                # отрезаем всё до заголовка
                if idx > 0:
                    del self.buf[:idx]
                # нужно как минимум: PH(2) + CT(1) + LSN(1) + FSA(2) + LSA(2) + CS(2) = 10 байт
                if len(self.buf) < 10:
                    # дочитка
                    self._read_to_buffer(512)
                    if len(self.buf) < 10 and (time.time() - start_time) > wait_timeout:
                        return None
                # теперь распарсим по формату
                # PH already at buf[0:2]
                # читаем CT, LSN, FSA, LSA, CS
                # формат маленький endian (см. мануал)
                try:
                    # убедимся что в буфере хотя бы минимальный заголовок
                    header = bytes(self.buf[:10])
                    # unpack: PH(2), CT(1), LSN(1), FSA(2), LSA(2), CS(2)
                    # но PH мы уже знаем, читая с 0
                    # берем CT .. CS
                    ct = header[2]
                    lsn = header[3]
                    fsa = struct.unpack_from('<H', header, 4)[0]
                    lsa = struct.unpack_from('<H', header, 6)[0]
                    cs_field = struct.unpack_from('<H', header, 8)[0]
                except Exception as e:
                    # нечего парсить пока
                    if (time.time() - start_time) > wait_timeout:
                        return None
                    self._read_to_buffer(512)
                    continue

                # теперь ожидаем полные данные: каждый sample Si = 2 байта, всего lsn * 2
                total_packet_len = 2 + 1 + 1 + 2 + 2 + 2 + (lsn * 2)  # PH + CT + LSN + FSA + LSA + CS + samples
                if len(self.buf) < total_packet_len:
                    # дочитаем
                    self._read_to_buffer(total_packet_len - len(self.buf) + 64)
                    if len(self.buf) < total_packet_len and (time.time() - start_time) > wait_timeout:
                        return None

                if len(self.buf) >= total_packet_len:
                    packet = bytes(self.buf[:total_packet_len])

                    # всё ок, парсим samples
                    samples = []
                    offset = 10
                    for i in range(lsn):
                        if offset + 2 > len(packet):
                            break
                        si = struct.unpack_from('<H', packet, offset)[0]  # little-endian
                        offset += 2
                        samples.append(si)
                    # удаляем пакет из буфера
                    del self.buf[:total_packet_len]

                    # теперь преобразуем в углы и расстояния
                    angle_fsa = ((fsa >> 1) / 64.0)  # degrees
                    angle_lsa = ((lsa >> 1) / 64.0)  # degrees

                    # diff angle (clockwise difference) — учтём поворот через 360
                    diff = angle_lsa - angle_fsa
                    if diff < 0:
                        diff += 360.0

                    points = []
                    for i, si in enumerate(samples, start=1):
                        # Distance formula: Distance_i = Si / 4  (мм).
                        dist_mm = si / 4.0
                        # first-level angle
                        if lsn == 1:
                            angle_i = angle_fsa
                        else:
                            angle_i = (diff / (lsn - 1)) * (i - 1) + angle_fsa
                        # second-level correction (manually from doc):
                        if dist_mm == 0:
                            ang_corr_deg = 0.0
                        else:
                            ang_corr_rad = math.atan(21.8 * (155.3 - dist_mm) / (155.3 * dist_mm))
                            ang_corr_deg = math.degrees(ang_corr_rad)
                        angle_corr = angle_i + ang_corr_deg
                        # normalize angle into [0,360)
                        angle_corr = angle_corr % 360.0
                        points.append({
                            'angle': angle_corr,
                            'value': dist_mm
                        })
                    return points
            else:
                # заголовок не найден — дочитываем и ждём
                self.buf.clear()
                self._read_to_buffer(512)
            if (time.time() - start_time) > wait_timeout:
                return None

    def stream_scans(self, callback=None):
        """Непрерывно читает пакеты и вызывает callback(points) для каждого пакета.
           Если callback None — печатает кратко."""
        try:
            while True:
                pts = self.read_scan_packet(wait_timeout=1.0)
                if pts is None:
                    continue
                if callback:
                    callback(pts)
                else:
                    print(f"Got {len(pts)} points; first: angle={pts[0]['angle']:.2f}° dist={pts[0]['value']:.2f}mm")
        except KeyboardInterrupt:
            print("Stop stream.")

def save_points_csv(points, filename):
    """points = list of dicts как выше"""
    keys = ['angle', 'value']
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for p in points:
            writer.writerow({k: p[k] for k in keys})

# Пример использования:
if __name__ == '__main__':
    lidar = YDLidarX2('/dev/ttyUSB0', baudrate=115200, timeout=0.5)  # замените порт
    try:
        def cb(pts):
            print(f"Packet: {len(pts)} pts, sample angles: {[round(p['angle'],1) for p in pts[:5]]}")
            # сохраняем последний пакет в csv
            save_points_csv(pts, '/home/pi/last_scan.csv')
        lidar.stream_scans(callback=cb)
    finally:
        lidar.close()