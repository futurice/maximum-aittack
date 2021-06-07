# EDIT THIS FILE

# InvaderBot is a simple helper class which has methods to control the robot.
# It offers an interface over Webots' default motor controller.
# You can use it, modify it or you can also use Webots' own commands.
# Using the helper class is recommended because it will later help you to
# transfer your code into a physical robot, which is running on Raspberry Pi.

# Inspired by https://medium.com/@abhishek.bn93/using-keras-reinforcement-learning-api-with-openai-gym-6c2a35036c83

import sys

import keras.callbacks

from keras.models import Sequential
from keras.layers import Dense, Flatten

from rl.agents import SARSAAgent
from rl.policy import EpsGreedyQPolicy
from rl.agents import DDPGAgent

from rally_env_just_speed import RallyEnv


# Reward function gets a deque of observations and the amount of steps after the last reset
# observations[len(observations) - 1]
# observations[0] for the oldest
def calculate_reward(time, length):
    # simple interpolation
    target_length = 500
    target_time = 40

    length_m = length * 100
    time_s = time * 10

    time_at_length = (target_time * length_m) / target_length

    return (target_time / time_at_length) * length


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


def train():

    env = RallyEnv()

    print('OBS', env.observation_space.spaces["state"])
    print('n', env.action_space)

    model = agent(env.observation_space.spaces["state"], env.action_space)

    policy = EpsGreedyQPolicy()

    sarsa = SARSAAgent(model=model, policy=policy, nb_actions=env.action_space)

    sarsa.compile('adam', metrics=['mse'])

    sarsa.fit(env, nb_steps=50000, visualize=False, verbose=1, callbacks=callbacks)

    sarsa.save_weights('sarsa_weights_final.h5f', overwrite=True)


train()
