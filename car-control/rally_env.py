import numpy as np
import gym
from gym import spaces
from gym.utils import seeding

import telemetry
import screencap
import keys
import joystick

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
MAX_STEPS = 5000

WIDTH = 120
HEIGHT = 80

T_LENGTH = 0.0700
T_TIME = 60.0


def default_reward(time, length, speed):
    # simple interpolation

    length_m = length * 100

    time_at_length = (T_TIME * length_m) / T_LENGTH

    print("Length", length)

    if time_at_length == 0:
        return speed * 1000

    return (time / time_at_length) * length * 1000


class RallyEnv(gym.Env):
    """
    OpenAI Gym Environment
    """

    def __init__(self, track_reward=default_reward, target_length=T_LENGTH, max_steps=MAX_STEPS):
        print("Starting Rally Env")

        self.track_reward = track_reward
        self.target_length = target_length

        # Throttle, steering
        self.action_space = spaces.Box(low=np.array([0.5, -1]), high=np.array([1, 1]), dtype=np.float32)

        # self.observation_space = spaces.Dict({
        #    'observation': spaces.Box(low=0, high=255, shape=(WIDTH, HEIGHT, 3), dtype=np.uint8),
        #    'camera': spaces.Box(low=0, high=255, shape=(WIDTH, HEIGHT, 3), dtype=np.uint8),
        #    # Speed, and angle
        #    'state': spaces.Box(low=np.array([0, -1]), high=np.array([300, 1]), dtype=np.float32)
        #})

        self.observation_space = spaces.Box(low=np.array([0, -1]), high=np.array([300, 1]), dtype=np.float32)

        # game world data
        # simulation related variables.
        self.seed()

        self.steps = 0
        self.max_steps = max_steps

        # Init inputs
        joystick.set_throttle(0.5)
        joystick.set_steering(0.5)
        keys.start()
        print('RallyEnv created')

    def __del__(self):
        self.close()

    def close(self):
        print('No quitters here')

    def seed(self, seed=None):
        np_random, seed = seeding.np_random(seed)
        return [seed]

    def calculate_done(self, speed, length, steps):
        # Simple crash detection
        if steps > 150 and speed < 0.5:
            return True

        return self.steps > self.max_steps or length >= self.target_length

    def step(self, action):
        self.steps += 1

        telemetry.update()
        img = screencap.capture_screen_py()

        joystick.set_throttle(action[0])
        joystick.set_steering(action[1])

        length = telemetry.get_telemetry_value("m_totalDistance")
        angle = telemetry.get_telemetry_value("m_steer")
        speed = telemetry.get_telemetry_value("m_speed")
        time = telemetry.get_telemetry_value("m_time")

        self.last_img = img

        reward = self.track_reward(time, length, speed)

        print("reward", reward, action[0])

        done = self.calculate_done(speed, length, self.steps)

        if done:
            print("It is done")

        observation = {
            'camera': np.array(img),
            'state': np.array([speed, angle])
        }

        return np.array([speed, angle]), reward, done, {}

    def reset(self):
        print('Resetting!')

        self.steps = 0
        joystick.set_steering(0.5)
        joystick.set_throttle(0.5)
        keys.reset()
        telemetry.reset()
        keys.start()

        print('Reset Done')

        return np.array([0, 0])

    def render(self, mode='human'):
        # render the image
        pass
