#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    record.py
"""

import errno
import os
import numpy as np
from datetime import datetime
import time
import signal
from mss import mss

from PIL import Image
from docopt import docopt

from cffi import FFI

import controller
import telemetry

# Optimus laptop fails native screengrab, so include a slower option
disable_native_grab = True
bbox = {'top': 72, 'left': 0, 'width': 1280, 'height': 720}

from enum import Enum, auto
class State(Enum):
    WAITING = auto()
    DRIVING = auto()
    CRASHED = auto()
    ERROR = auto()

def getImageName(id):
    return 'shot_{0}.png'.format(id)

def capture_screen(ffi, msc, id, path):
    start_time = datetime.now()
    width = msc.get_capture_width()
    height = msc.get_capture_height()
    bytes = msc.get_bytes_per_pixel()
    buffer_size = width * height * bytes
    buffer = np.empty((buffer_size), np.uint8)
    capture_result = msc.capture_frame(ffi.cast("uint8_t *", buffer.ctypes.data))
    if capture_result < 0:
        # see https://docs.microsoft.com/en-us/windows/desktop/direct3ddxgi/dxgi-error. Especially 0x887A0027 (DXGI_ERROR_WAIT_TIMEOUT) can happen
        # if there was no new frame available since the last frame captured
        print(ffi.string(msc.get_last_error()))
        return
    capture_time = datetime.now()

    img = Image.frombytes("RGB", (width, height), buffer, "raw", "BGRX")
    filename = path + getImageName(id)
    img.save(filename)
    save_time = datetime.now()
    print('capture time:', (capture_time - start_time).microseconds / 1000, ', save time:',
          (save_time - capture_time).microseconds / 1000)

def capture_screen_py(sct, id, path):
    sct_img = sct.grab(bbox)
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    resized = img.resize((240, 168))
    filename = path + getImageName(id)
    resized.save(filename, compress_level=1)

def captureJoystick(id, path, speed):
    imageName = getImageName(id)
    steering, throttle, brake = controller.getXZ()
    with open(path + ('record_%d.json' % id), 'w') as f:
        f.write(
            '{"cam/image_array":"%s","telemetry/speed":%f,"user/throttle":%f,"user/angle":%f,"user/brake":%f,"user/mode":"user"}' % (
            imageName, speed, throttle, steering, brake))


def get_record_path():
    return './log/tub_' + str(time.time()) + '/'

def exit_gracefully(signum, frame):
    print('EXIT SIGNAL')
    quit()

def record():
    global disable_native_grab
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    time.sleep(5)

    state = State.WAITING
    recordPath = '.'
    if (disable_native_grab == False):
        ffi = FFI()
        mscLib = ffi.dlopen('msc_x64.dll')
        ffi.cdef('''
            int init();
            void close();
            int get_capture_width();
            int get_capture_height();
            int get_bytes_per_pixel();
            int capture_frame(uint8_t* buffer);
            const char* get_last_error();
        ''')
        ret = mscLib.init()
        print(ret)
        print(ffi.string(mscLib.get_last_error()))
    else:
        sct = mss()

    # if not os.path.exists(os.path.dirname(recordPath)):
    # try:
    #     os.makedirs(os.path.dirname(recordPath))
    # except OSError as exc:  # Guard against race condition
    #     if exc.errno != errno.EEXIST:
    #         print('Recording name already exists. Please use another one')
    #         raise
    # else:
    #     print('Recording name already exists. Please use another one')
    #     exit(1)


    try:
        counter = 0
        id = 0
        prevSec = datetime.now().time().second
        while True:
            # Excplicit update call because I'm lazy
            telemetry.update()
            speed = telemetry.get_telemetry_value('m_speed') * 3.6
            laptime = telemetry.get_telemetry_value('m_lapTime')
            g_lat = telemetry.get_telemetry_value('m_gforce_lat')
            g_lon = telemetry.get_telemetry_value('m_gforce_lon')

            if (laptime > 0 and state == State.WAITING):
                print('Driving started')
                counter = 0
                state = State.DRIVING
                recordPath = get_record_path()
                try:
                    os.makedirs(os.path.dirname(recordPath))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        print('Recording name already exists. Please use another one')
                        raise
                with open(recordPath + 'meta.json', 'w') as f:
                    f.write(
                        '{"inputs":['
                        '"cam/image_array",'
                        '"telemetry/speed",'
                        '"user/throttle",'
                        '"user/angle",'
                        '"user/brake",'
                        '"user/mode"],'
                        '"types":['
                        '"image_array",'
                        '"float",'
                        '"float",'
                        '"float",'
                        '"float",'
                        '"str"]}')

                # print(laptime)
            elif (laptime == 0 and state != State.WAITING):
                print('New lap starting')
                state = State.WAITING
            elif (state == State.WAITING):
                print('Waiting for start')

            if (g_lat > 6 or g_lon > 6):
                # state = State.CRASHED
                print('Crashed', g_lon, g_lat)

            if (state == State.DRIVING):
                # print(speed, g_lon, g_lat)
                captureJoystick(counter, recordPath, speed)
                if (disable_native_grab):
                    capture_screen_py(sct, counter, recordPath)
                else:
                    capture_screen(ffi, mscLib, counter, recordPath)



            id = id + 1
            counter = counter + 1
            currSec = datetime.now().time().second
            if currSec is not prevSec:
                print('Change', id, 'fps')
                id = 0
            prevSec = currSec
            # sleep(0.1)
    except Exception as e:
        print('\a')
        time.sleep(1)
        print('\a')
        time.sleep(1)
        print('\a')
        quit()


if __name__ == '__main__':
    args = docopt(__doc__)
    record()
