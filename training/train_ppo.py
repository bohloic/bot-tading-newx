from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import pandas as pd

from training.env.trading_env import TradingEnv

df = pd.read_csv("data/market_data.csv")

env = DummyVecEnv([lambda: TradingEnv(df)])

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    tensorboard_log="./logs"
)

model.learn(total_timesteps=500_000)

model.save("models/ppo_latest.zip")