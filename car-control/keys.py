import time
from pynput.keyboard import Key, KeyCode, Controller

keyboard = Controller()


def click(key):
    keyboard.press(key)
    time.sleep(0.1)
    keyboard.release(key)
    time.sleep(0.1)


def reset():
    click(Key.esc)
    click(Key.down)
    click(Key.enter)
    click(Key.up)
    click(Key.enter)


def start():
    time.sleep(5)
    keyboard.press(Key.space)
    time.sleep(1)
    keyboard.release(Key.space)
    time.sleep(5)


def press_throttle():
    keyboard.press("a")


def release_throttle():
    keyboard.release("a")


def press_left():
    keyboard.press(",")


def release_left():
    keyboard.release(',')


def press_right():
    keyboard.press(".")


def release_right():
    keyboard.release('.')


#print("Go")

#release_throttle()

#print("double press")
#press_throttle()
#press_throttle()
#print("Done")
# time.sleep(5)
# reset()
# start()

# print("Done")
