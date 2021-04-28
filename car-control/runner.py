import gym
from gym.envs.registration import register

register(
    id="rally-v0",
    entry_point="rally_env:aRallyEnv",
)

env = gym.make("rally-v0")

for i_episode in range(20):
    observation = env.reset()
    for t in range(10000):
        env.render()
        # print(observation.state)
        # print(observation)
        action = env.action_space.sample()
        print('The action')
        observation, reward, done, info = env.step(action)
        if done:
            print("Episode finished after {} timesteps".format(t+1))
            break

env.close()