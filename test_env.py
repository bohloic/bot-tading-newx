import pandas as pd
import numpy as np

from app.ai.environment.trading_env import TradingEnv


# Fake dataset
rows = 500

df = pd.DataFrame({

    "close": np.random.random(rows) * 100,

    "rsi": np.random.random(rows) * 100,

    "rsi_price_line": np.random.random(rows) * 100,

    "rsi_signal_line": np.random.random(rows) * 100,

    "mbl": np.random.random(rows) * 100,

    "volume": np.random.random(rows) * 1000,
})

env = TradingEnv(df)

obs, _ = env.reset()

done = False

while not done:

    action = env.action_space.sample()

    obs, reward, done, _, info = env.step(action)

    print(
        f"Reward: {reward:.2f} | "
        f"Balance: {info['balance']:.2f}"
    )