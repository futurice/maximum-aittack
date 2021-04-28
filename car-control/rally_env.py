import numpy as np
import gym
from gym import spaces
from gym.utils import seeding


import telemetry
import screencap
import keys

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
MAX_STEPS = 5000

WIDTH = 120
HEIGHT = 80


class RallyEnv(gym.Env):
    """
    OpenAI Gym Environment
    """

    def __init__(self, max_steps=MAX_STEPS):
        print("starting Rally Env")

        # Left and right
        self.action_space = spaces.Discrete(3)

        self.observation_space = spaces.Dict({
            'camera': spaces.Box(low=0, high=255, shape=(WIDTH, HEIGHT, 3), dtype=np.uint8),
            # Speed, and angle
            'state': spaces.Box(low=np.array([0, -1]), high=np.array([300, 1]), dtype=np.float32)
        })
        # game world data
        # simulation related variables.
        self.seed()

        self.steps = 0
        self.max_steps = max_steps

        keys.start()

    def __del__(self):
        self.close()


    def close(self):
        print('No quitters here')

    def seed(self, seed=None):
        np_random, seed = seeding.np_random(seed)
        return [seed]

    def calculate_done(self, speed, steps):
        if steps > 100 and speed < 0.5:
            return True

        return self.steps > self.max_steps

    def step(self, action):
        self.steps += 1
        if self.steps % 3 == 0:
            keys.release_throttle()
        else:
            keys.press_throttle()

        if action == 0:
            keys.release_right()
            keys.press_left()

        if action == 1:
            keys.release_left()
            keys.release_right()

        if action == 2:
            keys.release_left()
            keys.press_right()

        telemetry.update()
        img = screencap.capture_screen_py()

        length = telemetry.get_telemetry_value("m_totalDistance")
        angle = telemetry.get_telemetry_value("m_steer")
        speed = telemetry.get_telemetry_value("m_speed")

        self.last_img = img

        reward = length
        self.points += reward

        done = self.calculate_done(speed, self.steps)

        if done:
            print("It is done")

        obs = {
            'camera': np.array(img),
            'state': np.array([speed, angle])
        }

        return obs, reward, done, {}

    def reset(self):
        print('reset')
        # reset joystcik
        # reset command
        keys.release_throttle()
        keys.release_left()
        keys.release_right()
        self.steps = 0
        keys.reset()
        telemetry.reset()
        keys.start()
        return {'camera': None, 'state': np.array([0, 0])}

    def render(self, mode='human'):
        # render the image
        pass
