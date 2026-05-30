import os
from stable_baselines3 import PPO

MODEL_PATH = "models/ppo_latest.zip"

model = None

if os.path.exists(MODEL_PATH):
    model = PPO.load(MODEL_PATH)
else:
    print("⚠️ Model not found, running in SAFE MODE")