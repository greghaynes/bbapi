from pathlib import Path
import select


class GPIOPin:
    def __init__(self, pin_number):
        self.pin_number = pin_number

    def __enter__(self):
        self._export()
        self._set_direction()
        self._set_edge()
        return self

    def __exit__(self, *args, **kwargs):
        self._unexport()

    def _export(self):
        with open('/sys/class/gpio/export', 'w') as fh:
            fh.write('%d' % self.pin_number)

    def _set_edge(self):
        with open(str(self._sysfs_pin_dir / 'edge'), 'w') as fh:
            fh.write('both')

    def _set_direction(self):
        try:
            with open(str(self._sysfs_pin_dir / 'direction'), 'w') as fh:
                fh.write('in')
        except OSError as e:
            if e.errno != 16:
                raise

    def _unexport(self):
        with open('/sys/class/gpio/unexport', 'w') as fh:
            fh.write('%d' % self.pin_number)

    @property
    def _sysfs_pin_dir(self):
        return Path('/sys/class/gpio/gpio%d' % self.pin_number)

    @property
    def value_path(self):
        return self._sysfs_pin_dir / 'value'

    def value(self):
        with open(str(self.value_path), 'r') as fh:
            raw_val = fh.read()
            return int(raw_val)


class PinPoller:
    def __init__(self):
        self._fd_pin_fh_map = {}
        self._poller = select.epoll()

    def watchPin(self, pin):
        fh = open(str(pin.value_path), 'r')
        fd = fh.fileno()
        self._fd_pin_fh_map[fd] = (pin, fh)
        self._poller.register(fd, select.EPOLLPRI | select.EPOLLET)

    def handle_pin_event(self, pin, fh, event):
        pass

    def poll_once(self, timeout_msecs=1000):
        poll_evs = self._poller.poll(timeout_msecs)
        for fd, poll_ev in poll_evs:
            pin, fh = self._fd_pin_fh_map[fd]
            self.handle_pin_event(pin, fh, poll_ev)


class EchoPoller(PinPoller):
    def handle_pin_event(self, pin, fh, event):
        if event & select.EPOLLET == select.EPOLLET:
            print("Error")
        if event & select.EPOLLPRI == select.EPOLLPRI:
            print("Pin %d changed" % pin.pin_number)


if __name__ == '__main__':
    poller = EchoPoller()
    with GPIOPin(20) as pin:
        poller.watchPin(pin)
        while True:
            poller.poll_once()
