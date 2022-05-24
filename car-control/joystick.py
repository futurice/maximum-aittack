import pyvjoy
import time

j = pyvjoy.VJoyDevice(1)


def set_throttle(value):
    scaled_value = int(1 + (value * (0x8000 - 1)))
    # print('Throttle: ', scaled_value)
    j.set_axis(pyvjoy.HID_USAGE_RZ, scaled_value)


def set_steering(value):
    scaled_value = int(((1 + value) / 2) * 0x8000)
    # print('Steering: ', scaled_value)
    j.set_axis(pyvjoy.HID_USAGE_RX, scaled_value)


def reset():
    j.reset()
    j.reset_buttons()
    j.reset_povs()


def calibrate():
    j.reset()
    print("Start timer 5s")
    time.sleep(5)
    print('Accelerate')
    set_throttle(1)
    print('Brake')
    time.sleep(3)
    set_throttle(0)
    print('Left')
    time.sleep(5)
    set_steering(-0.5)
    print('Right')
    time.sleep(5)
    set_steering(1)
    print('Done')
    set_steering(0)
    j.reset()


# calibrate()