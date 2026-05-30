import gymnasium as gym
import numpy as np
from gymnasium import spaces


class TradingEnv(gym.Env):
    def __init__(self, df):
        super().__init__()

        self.df = df.reset_index(drop=True)

        self.action_space = spaces.Discrete(3)

        # normalized features (IMPORTANT)
        self.observation_space = spaces.Box(
            low=0,
            high=1,
            shape=(5,),
            dtype=np.float32
        )

        self.initial_balance = 10_000

        self.reset()

    # ================= RESET =================
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        self.current_step = 50

        self.peak = self.balance

        return self._obs(), {}

    # ================= OBS =================
    def _obs(self):
        row = self.df.iloc[self.current_step]

        obs = np.array([
            row["Price_Close"],
            row["TDI_RSI_Line"],
            row["TDI_Market_Baseline"],
            row["TDI_Vol_Bands"],
            row["Volume"]
        ], dtype=np.float32)

        return np.nan_to_num(obs)

    # ================= STEP =================
    def step(self, action):

        row = self.df.iloc[self.current_step]
        price = float(row["Price_Close"])

        reward = 0.0

        # ================= HOLD COST (soft) =================
        reward -= 0.0002

        # ================= BUY =================
        if action == 1 and self.position == 0:
            self.position = 1
            self.entry_price = price

        # ================= SELL =================
        elif action == 2 and self.position == 1:

            pnl = (price - self.entry_price) / self.entry_price

            self.balance *= (1 + pnl)

            self.position = 0
            self.entry_price = 0

            # log reward (stabilisé)
            reward += np.tanh(pnl * 10)

        # ================= DRAW DOWN CONTROL =================
        self.peak = max(self.peak, self.balance)
        dd = (self.peak - self.balance) / self.peak

        reward -= dd * 2.0  # penalité progressive (PRO)

        # ================= TERMINATION =================
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1

        return self._obs(), reward, done, False, {}