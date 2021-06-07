#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    drive.py (drive) [--model=<model>]
    drive.py (reset)
    drive.py (throttle)
    drive.py (steering)

"""
import os
import numpy

from docopt import docopt
from PIL import Image
from time import sleep, time
import mss
import pyvjoy
import collections
import joystick


# import parts
from donkeycar.parts.keras import KerasCategorical


def captureScreen(sct):
    img = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
    return img.resize((160, 120))


def drive(model_path=None):
    kl = KerasCategorical()
    if model_path:
        kl.load(model_path)
    print('Model loaded')
    # testImage = Image.open('test.png');
    # testImage = numpy.array(testImage)

    throttle_history = collections.deque(maxlen=10)
    angle_history = collections.deque(maxlen=10)
    for i in range(10):
        throttle_history.append(0)
        angle_history.append(0)
    print(len(throttle_history))
    print(len(angle_history))
    round = 0
    while True:
        with mss.mss() as sct:
            image = captureScreen(sct)
            image = numpy.array(image)
            if (round > 0):
                angle, throttle = kl.run(image, prevImage, numpy.array(angle_history), numpy.array(throttle_history))

                # print('Raw throttle', throttle)
                # throttle = min(0.8, max(0.1, throttle * 3000000))

                joystick.set_throttle(throttle)
                joystick.set_steering(angle)
                # s = input(">>")
                # if len(s) >= 1:
                #    break
                # if (round % 100 == 0):
                # print(throttle, angle)
                throttle_history.append(throttle)
                angle_history.append(angle)

            prevImage = image
            round = round + 1

        # V.add(kl, inputs=['cam/image_array'],
        #          outputs=['pilot/angle', 'pilot/throttle'],
        #          run_condition='run_pilot')


if __name__ == '__main__':
    try:
        args = docopt(__doc__)
        if args['throttle']:
            print("Pressing throttle")
            while (True):
                for x in range(0, 100):
                    joystick.set_throttle(x * 0.01)
                    sleep(0.01)
                for x in range(100, 0):
                    joystick.set_throttle(x * 0.01)
                    sleep(0.01)

        if args['steering']:
            print("Steering")
            while (True):
                for x in range(-100, 100):
                    joystick.set_steering(x * 0.01)
                    sleep(0.01)

        if args['drive']:
            print('Reset axis')
            joystick.set_throttle(0)
            joystick.set_steering(0)
            print("Starting driving")
            drive(model_path=args['--model'])
        elif args['reset']:
            joystick.set_throttle(0)
            joystick.set_steering(0)
    except Exception as e:
        joystick.set_throttle(0)
        joystick.set_steering(0)
        raise (e)
