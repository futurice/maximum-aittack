import ctypes
import time
from sdl2 import *

class Joystick:
    def __init__(self):
        SDL_Init(SDL_INIT_JOYSTICK)
        self.axis = {}
        self.button = {}

    def update(self):
        event = SDL_Event()
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_JOYDEVICEADDED:
                self.device = SDL_JoystickOpen(event.jdevice.which)
            elif event.type == SDL_JOYAXISMOTION:
                self.axis[event.jaxis.axis] = event.jaxis.value

joystick = Joystick()
        
def getXZ():
    joystick.update()
    leftMushroomX = joystick.axis.get(0)
    leftMushroomX = 0 if leftMushroomX is None else leftMushroomX / 32768
    rightTrigger = joystick.axis.get(5)
    rightTrigger = 0 if rightTrigger is None else (rightTrigger + 32767) / 65536
    leftTrigger = joystick.axis.get(2)
    leftTrigger = 0 if leftTrigger is None else (leftTrigger + 32767) / 65536
    return round(leftMushroomX, 2), round(rightTrigger, 2), round(leftTrigger, 2)

