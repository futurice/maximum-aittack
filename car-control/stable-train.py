import gym
from gym.envs.registration import register

from stable_baselines3 import PPO

register(
    id="rally-v0",
    entry_point="rally_env:RallyEnv",
)

# Create the environment
env = gym.make("rally-v0")

print(env.action_space)
print(env.observation_space)

# Define the model
model = PPO("MlpPolicy", env, verbose=1)
# model = PPO.load("carcontrol", env)

# Train the agent
model.learn(total_timesteps=3000)
model.save("carcontrol")

# After training, watch our agent walk
obs = env.reset()
print("Start driving")
for i in range(2000):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    env.render()
print("End Driving")
