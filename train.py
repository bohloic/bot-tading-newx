from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
import pandas as pd

from app.ai.environment.trading_env import TradingEnv


df = pd.read_csv("data/market_data.csv")

# env
env = DummyVecEnv([lambda: TradingEnv(df)])
env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)

eval_env = DummyVecEnv([lambda: TradingEnv(df)])
eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

# callback PRO
eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="./models/best/",
    log_path="./logs/eval/",
    eval_freq=5000,
    deterministic=True
)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    tensorboard_log="./logs"
)

model.learn(
    total_timesteps=500_000,
    callback=eval_callback
)

model.save("models/final_trading_model")