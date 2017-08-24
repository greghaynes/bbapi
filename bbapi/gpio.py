from pathlib import Path


class GPIOPin:
    def __init__(self, pin_number):
        self.pin_number = pin_number
        self.value_fh = None

    def __enter__(self):
        self._export()
        self._set_edge()
        self.value_fh = open(str(self._sysfs_pin_dir / 'value'), 'r')
        return self

    def __exit__(self, *args, **kwargs):
        if self.value_fh is not None:
            self.value_fh.close()
            self.value_fh = None
        self._unexport()

    def _export(self):
        with open('/sys/class/gpio/export', 'w') as fh:
            fh.write('%d' % self.pin_number)

    def _set_edge(self):
        with open(str(self._sysfs_pin_dir / 'edge'), 'w') as fh:
            fh.write('both')

    def _unexport(self):
        with open('/sys/class/gpio/unexport', 'w') as fh:
            fh.write('%d' % self.pin_number)

    @property
    def _sysfs_pin_dir(self):
        return Path('/sys/class/gpio/gpio%d' % self.pin_number)

    def value(self):
        with open(str(self._sysfs_pin_dir / 'value'), 'r') as fh:
            raw_val = fh.read()
            return int(raw_val)


if __name__ == '__main__':
    with GPIOPin(20) as pin:
        print(pin.value())
