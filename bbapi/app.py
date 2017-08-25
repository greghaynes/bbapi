import contextlib
import threading

from aiohttp import web

from bbapi import gpio


class _UpdateValuesPoller(gpio.PinPoller):
    def __init__(self, pin_values):
        super(_UpdateValuesPoller, self).__init__()
        self._pin_values = pin_values

    def handle_pin_event(self, pin, fh, event):
        self._pin_values.update_pin(pin)


class PinValues:
    def __init__(self, gpio_pins=None):
        self._gpio_pins = gpio_pins or []
        self._pin_vals = {}
        self._stop = True
        self._poll_thread = threading.Thread(target=self._poll_pins, name='poll_pins')

    def _poll_pins(self):
        self._stop = False
        poller = _UpdateValuesPoller(self)
        with contextlib.ExitStack() as cm_stack:
            pins = [cm_stack.enter_context(pin) for pin in self._gpio_pins]
            for pin in pins:
                self.update_pin(pin)
                poller.watchPin(pin)
            while not self._stop:
                poller.poll_once()

    @property
    def all_pins(self):
        return self._pin_vals

    def update_pin(self, pin):
        new_val = pin.value()
        if new_val != self._pin_vals.get(pin.pin_number):
            self._pin_vals[pin.pin_number] = new_val
            self.handle_pin_changed(pin)

    def start_polling(self):
        self._poll_thread.start()

    def stop_polling(self):
        self._stop =  True
        self._poll_thread.join()

    def handle_pin_changed(self, pin):
        print('pins updated: %s' % self._pin_vals)


class WebHandlers:
    def __init__(self, pin_values):
        self._pin_values = pin_values

    async def all_pins(self, request):
        return web.json_response(self._pin_values.all_pins)


class WebApp:
    def __init__(self, pin_values):
        self._pin_values = pin_values
        self.aio_app = web.Application()
        self._handlers = WebHandlers(pin_values)
        self.add_routes()

    def add_routes(self):
        self.aio_app.router.add_get('/pins/all', self._handlers.all_pins)

    def run(self):
        web.run_app(self.aio_app, port=8800)


if __name__ == '__main__':
    pins = [gpio.GPIOPin(20), gpio.GPIOPin(66)]
    vals = PinValues(pins)
    vals._poll_pins()
