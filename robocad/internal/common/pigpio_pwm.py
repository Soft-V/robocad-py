import os
import select
import stat
import time
from threading import RLock


class PigpioPWM:
    """PWM through pigpiod's text FIFOs; one controlling application at a time."""

    PWM_RANGE = 10000

    def __init__(self, pipe_path='/dev/pigpio', response_path='/dev/pigout',
                 frequency=100, timeout=1.0):
        if not isinstance(frequency, int) or frequency <= 0:
            raise ValueError('PWM frequency must be a positive integer')
        if not 0 < timeout < float('inf'):
            raise ValueError('pigpio timeout must be positive and finite')
        self.pipe_path = pipe_path
        self.response_path = response_path
        self.frequency = frequency
        self.timeout = timeout
        self._pipe_identity = None
        self._configured = set()
        self._used = set()
        self._stopped = False
        self._lock = RLock()

    @staticmethod
    def _open_fifo(path, mode):
        # No O_CREAT: a missing daemon must never produce an ordinary file.
        fd = os.open(path, mode | os.O_NONBLOCK)
        if not stat.S_ISFIFO(os.fstat(fd).st_mode):
            os.close(fd)
            raise RuntimeError(f'{path} is not a pigpio FIFO')
        return fd

    def _command(self, command_fd, response_fd, command):
        data = (command + '\n').encode('ascii')
        if os.write(command_fd, data) != len(data):
            raise RuntimeError('Incomplete write to pigpio FIFO')

        deadline = time.monotonic() + self.timeout
        response = bytearray()
        while b'\n' not in response:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([response_fd], [], [], remaining)[0]:
                raise RuntimeError(f'Timed out waiting for pigpiod: {command}')
            chunk = os.read(response_fd, 64)
            if not chunk:
                raise RuntimeError('pigpiod closed its response FIFO')
            response.extend(chunk)
        try:
            result = int(response)
        except ValueError as exc:
            raise RuntimeError(f'Invalid pigpio response: {response!r}') from exc
        if result < 0:
            raise RuntimeError(f'pigpio command {command!r} failed with error {result}')
        return result

    def set_dutycycle(self, gpio, duty):
        if not isinstance(gpio, int) or not 0 <= gpio <= 31:
            raise ValueError('pigpio GPIO must be an integer from 0 to 31')
        if not 0.0 <= duty <= 1.0:
            raise ValueError('PWM duty cycle must be between 0 and 1')

        with self._lock:
            if self._stopped and duty != 0:
                raise RuntimeError('PWM controller has been stopped')
            command_fd = response_fd = None
            try:
                command_fd = self._open_fifo(self.pipe_path, os.O_WRONLY)
                response_fd = self._open_fifo(self.response_path, os.O_RDONLY)
                info = os.fstat(command_fd)
                identity = (info.st_dev, info.st_ino)
                if identity != self._pipe_identity:
                    self._configured.clear()
                    self._pipe_identity = identity

                # Discard replies left by a previous application. Each command
                # below consumes its own reply before sending the next one.
                while True:
                    try:
                        if not os.read(response_fd, 4096):
                            break
                    except BlockingIOError:
                        break

                if duty == 0:
                    # WRITE cancels PWM/servo generation and actively holds the
                    # signal LOW. Disabling must not depend on PWM configuration.
                    self._command(command_fd, response_fd, f'W {gpio} 0')
                    self._configured.discard(gpio)
                    self._used.discard(gpio)
                    return

                # A restarted daemon can reuse the same FIFO inode.
                if gpio in self._configured and (
                        self._command(command_fd, response_fd, f'PFG {gpio}') != self.frequency or
                        self._command(command_fd, response_fd, f'PRG {gpio}') != self.PWM_RANGE):
                    self._configured.discard(gpio)
                if gpio not in self._configured:
                    self._command(command_fd, response_fd, f'P {gpio} 0')
                    actual = self._command(command_fd, response_fd,
                                           f'PFS {gpio} {self.frequency}')
                    if actual != self.frequency:
                        raise RuntimeError(
                            f'pigpio selected {actual} Hz instead of {self.frequency} Hz; '
                            'check the pigpiod sample rate (100 Hz works with -s 5)')
                    self._command(command_fd, response_fd, f'PRS {gpio} {self.PWM_RANGE}')
                    self._configured.add(gpio)

                # Track the pin even if the daemon applies PWM but its reply is lost.
                self._used.add(gpio)
                self._command(command_fd, response_fd,
                              f'P {gpio} {round(duty * self.PWM_RANGE)}')
            except OSError as exc:
                self._configured.clear()
                raise RuntimeError(
                    f'Cannot communicate with pigpiod via {self.pipe_path}: {exc}. '
                    'Start pigpiod with its FIFO interface enabled and check FIFO permissions.') from exc
            except Exception:
                self._configured.clear()
                raise
            finally:
                if response_fd is not None:
                    os.close(response_fd)
                if command_fd is not None:
                    os.close(command_fd)

    def stop(self, gpios=None):
        """Disable the specified outputs, including any left by an earlier program.

        This removes control pulses; whether the servo releases torque without
        pulses depends on the servo. Nonzero PWM is rejected after stopping.
        """
        with self._lock:
            self._stopped = True
            errors = []
            targets = self._used.union(gpios if gpios is not None else ())
            for gpio in sorted(targets):
                try:
                    self.set_dutycycle(gpio, 0)
                except RuntimeError as exc:
                    errors.append(str(exc))
            if errors:
                raise RuntimeError('; '.join(errors))
