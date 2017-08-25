from bbapi import app as bbapp
from bbapi import gpio


def main():
    pins = [gpio.GPIOPin(20)]
    vals = bbapp.PinValues(pins)
    vals.start_polling()
    app = bbapp.WebApp(vals)
    app.run()
    vals.stop_polling()
