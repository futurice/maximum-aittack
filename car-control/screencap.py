#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    record.py
"""

import numpy as np
from datetime import datetime

from mss import mss

from PIL import Image

import time

# Optimus laptop fails native screengrab, so include a slower option
disable_native_grab = True
bbox = {'top': 72, 'left': 0, 'width': 1024, 'height': 768}
cbox = {'top': 320,'left': 0, 'right': 0, 'bottom': 0}

from enum import Enum, auto

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


sct = mss()

def capture_screen_py():
    sct_img = sct.grab(bbox)
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    resized = img.crop((0,320,1024,720)).resize((120, 80))
    return resized

if __name__ == '__main__':
    time.sleep(5)
    img = capture_screen_py()
    img.show()
    time.sleep(5)
    img = capture_screen_py()
    img.show()
