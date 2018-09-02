#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    record.py (--name=<name>)
"""

import errno
import os
from datetime import datetime
from time import sleep

from mss import mss
import mss.tools
from PIL import Image
from docopt import docopt

import controller


def getImageName(id):
    return 'shot_{0}.png'.format(id)


def captureScreen(sct, id, path):
    img = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
    resized = img.resize((160, 120))
    resized.save(path + getImageName(id))


def captureJoystick(id, path):
    imageName = getImageName(id)
    steering, throttle, brake = controller.getXZ()
    # print("steering", steering, "throttle", throttle, "throttlebrake", brake)
    with open(path + ('record_%d.json' % id), 'w') as f:
        f.write(
            '{"cam/image_array":"%s","user/throttle":%f,"user/angle":%f,"user/brake":%f,"user/mode":"user"}' % (
            imageName, throttle, steering, brake))


def record(name, limit=20000):
    print('Limiting recording to', limit)

    sleep(5)
    print('\a')

    recordPath = './log/' + name + '/'

    if not os.path.exists(os.path.dirname(recordPath)):
        try:
            os.makedirs(os.path.dirname(recordPath))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                print('Recording name already exists. Please use another one')
                raise
    else:
        print('Recording name already exists. Please use another one')
        exit(1)

    with open(recordPath + 'meta.json', 'w') as f:
        f.write(
            '{"inputs":["cam/image_array","user/angle","user/throttle","user/mode"],"types":["image_array","float","float","str"]}')

    try:
        with mss.mss() as sct:
            counter = 0
            id = 0
            prevSec = datetime.now().time().second
            while True:
                captureJoystick(counter, recordPath)
                captureScreen(sct, counter, recordPath)

                # thread = tick(counter, sct, counter)
                # thread.start()
                id = id + 1
                counter = counter + 1
                currSec = datetime.now().time().second
                if currSec is not prevSec:
                    print('Change', id, 'fps')
                    id = 0
                prevSec = currSec
                # sleep(0.1)
                if counter >= limit:
                    print('\a')
                    sleep(1)
                    print('\a')
                    sleep(1)
                    print('\a')
                    quit()
    except Exception as e:
        print('\a')
        sleep(1)
        print('\a')
        sleep(1)
        print('\a')
        raise e


if __name__ == '__main__':
    args = docopt(__doc__)
    record(args['--name'])
