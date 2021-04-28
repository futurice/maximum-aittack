# EDIT THIS FILE

# InvaderBot is a simple helper class which has methods to control the robot.
# It offers an interface over Webots' default motor controller.
# You can use it, modify it or you can also use Webots' own commands.
# Using the helper class is recommended because it will later help you to
# transfer your code into a physical robot, which is running on Raspberry Pi.

# Inspired by https://medium.com/@abhishek.bn93/using-keras-reinforcement-learning-api-with-openai-gym-6c2a35036c83

import sys

import keras.layers
import keras.models
import keras.callbacks

from keras.models import Sequential
from keras.layers import Dense, Flatten

from rl.agents import SARSAAgent
from rl.policy import EpsGreedyQPolicy
import math

from robo_env import RoboEnv


def point_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# Reward function gets a deque of observations and the amount of steps after the last reset
# observations[len(observations) - 1]
# observations[0] for the oldest
def calculate_reward(observations, steps):
    current_observation = observations[len(observations) - 1]
    oldest_observation = observations[0]
    # Start
    if current_observation is None:
        return 0
    # Give 10 points if the ball moves
    target_old = (oldest_observation[0], oldest_observation[1])
    target_curr = (current_observation[0], current_observation[1])
    bot_old = (oldest_observation[2], oldest_observation[3])
    bot_curr = (current_observation[2], current_observation[3])

    if point_distance(target_curr, target_old) > 0:
        # print('Ball moved!!!!')
        return 100
    # Give points of bot moves towards the target ball
    if len(observations) > 1:
        old_target_distance = point_distance(target_old, bot_old)
        curr_target_distance = point_distance(target_curr, bot_curr)
        # print(curr_target_distance - old_target_distance)
        if old_target_distance - curr_target_distance > 0.06:
            # print('\n', old_target_distance - curr_target_distance, '\n')
            return 1
    return 0


env = RoboEnv(calculate_reward)


def agent(states, actions):
    model = Sequential()
    model.add(Flatten(input_shape=(1, states)))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(actions, activation='linear'))
    return model


class SaveCallback(keras.callbacks.Callback):
    def _set_env(self, env):
        self.env = env

    def on_episode_begin(self, episode, logs={}):
        pass

    def on_episode_end(self, episode, logs={}):
        print(logs['episode_reward'])
        self.model.save_weights('sarsa_weights_%s_%s.h5f' % (episode, str(logs['episode_reward'])), overwrite=True)
        print('wrote: sarsa_weights_%s_%s.h5f' % (episode, str(logs['episode_reward'])))
        pass

    def on_step_begin(self, step, logs={}):
        pass

    def on_step_end(self, step, logs={}):
        pass

    def on_action_begin(self, action, logs={}):
        pass

    def on_action_end(self, action, logs={}):
        pass


callbacks = [
    SaveCallback()
]

model = agent(env.observation_space.shape[0], env.action_space.n)

policy = EpsGreedyQPolicy()

sarsa = SARSAAgent(model=model, policy=policy, nb_actions=env.action_space.n)

sarsa.compile('adam', metrics=['mse'])

sarsa.fit(env, nb_steps=5000000, visualize=False, verbose=1, callbacks=callbacks)

sarsa.save_weights('sarsa_weights_final.h5f', overwrite=True)

print('Hepskukkuu')
