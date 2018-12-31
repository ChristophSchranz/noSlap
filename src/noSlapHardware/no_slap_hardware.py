#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO  # import GPIO to use the Pins

# Set pins on places 7 and 8
LED_PIN = 4
BUTTON_PIN = 14


class noSlapHardware:
    def __init__(self):
        # initialize the GPIOs (General Purpose Input and Output)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # set the pins as output or input
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.setup(BUTTON_PIN, GPIO.IN)

    def light_on(self):
        GPIO.output(LED_PIN, True)
        print("Light is turned on.")

    def light_off(self):
        GPIO.output(LED_PIN, False)
        print("Light is turned out.")

    def button_status(self):
        status = not bool(GPIO.input(BUTTON_PIN))
        print("Status of the button is: {}".format(status))
        return status


if __name__ == "__main__":
    noslaphw = noSlapHardware()

    for _ in range(10):
        noslaphw.light_on()
        time.sleep(0.4)
        noslaphw.light_off()
        time.sleep(0.4)
        print(noslaphw.button_status())
