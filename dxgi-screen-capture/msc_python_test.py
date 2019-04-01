import time
from datetime import datetime

import numpy as np
from cffi import FFI
from PIL import Image

ffi = FFI()
msc = ffi.dlopen('msc_x64.dll')
ffi.cdef('''
    int init(unsigned int output_skip);
    void close();
    int get_capture_width();
    int get_capture_height();
    int get_bytes_per_pixel();
    int capture_frame(uint8_t* buffer);
    const char* get_last_error();
''')

buffer = None

def initialize(output_index):
    init_result = msc.init(output_index)

    if init_result == 0:
        width = msc.get_capture_width()
        height = msc.get_capture_height()
        bytes = msc.get_bytes_per_pixel()
        buffer_size = width * height * bytes
        global buffer
        buffer = np.empty((buffer_size), np.uint8)
        print('msc initialization successful!')
    else:
        print('msc initialization failed!')        
        print(msc.get_last_error())
    return init_result
    
def close():
    msc.close()
    global buffer
    buffer = None
    print('msc closed!')
    
def capture_screen(output_index, filename):
    capture_result = msc.capture_frame(ffi.cast("uint8_t *", buffer.ctypes.data))
    if capture_result == 0:
        width = msc.get_capture_width()
        height = msc.get_capture_height()
        img = Image.frombytes("RGB", (width, height), buffer, "raw", "BGRX")
        img.save(filename)
        save_time = datetime.now()
        print('saved', filename)
    # DXGI_ERROR_WAIT_TIMEOUT / 0x887A0027
    elif capture_result == -2005270489:
        print('no changes since last frame')
    # DXGI_ERROR_ACCESS_LOST / 0x887A0026
    # DXGI_ERROR_DEVICE_REMOVED / 0x887A0005
    # DXGI_ERROR_DEVICE_RESET / 0x887A0007
    elif capture_result == -2005270490 or  capture_result == -2005270523 or capture_result == -2005270521:
        print('attempting to reinitialize...')
        close()
        if initialization(0) == 0:
            print('reinitialization successful')
        else:
            print('reinitialization failed')
    else:
        print('capture failed!')

if initialize(0) == 0:
    i = 0
    while True:
        filename = 'shot{}.png'.format(i)
        capture_screen(0, filename)
        time.sleep(2)
        i += 1

    close()
