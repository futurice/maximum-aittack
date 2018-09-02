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
    leftMushroonX = joystick.axis.get(0)
    leftMushroonX = 0 if leftMushroonX is None else leftMushroonX
    rightTrigger = joystick.axis.get(5)
    rightTrigger = 0 if rightTrigger is None else rightTrigger
    leftTrigger = 0
    leftTrigger = 0 if leftTrigger is None else leftTrigger
    return leftMushroonX, rightTrigger, leftTrigger

