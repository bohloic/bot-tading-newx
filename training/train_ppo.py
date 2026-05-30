import os
import sys
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.logger import configure

# Sécurisation des chemins pour éviter les ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.env.advanced_trading_env import AdvancedTradingEnv

class TensorboardCallback(BaseCallback):
    """
    Callback personnalisé pour envoyer les métriques financières 
    (Equity, Max Drawdown) directement dans TensorBoard à chaque fin d'épisode.
    """
    def __init__(self, verbose=0):
        super(TensorboardCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        # On extrait les informations de l'environnement à la fin de chaque épisode
        for info in self.locals.get("infos", []):
            if "equity" in info:
                self.logger.record("custom/portfolio_equity", info["equity"])
            if "drawdown" in info:
                self.logger.record("custom/max_drawdown", info["drawdown"])
        return True


def load_historical_data(file_path: str) -> pd.DataFrame:
    """
    Charge et valide le dataset TDI d'origine.
    Format attendu : Timestamp | Price_Close | TDI_RSI_Line | TDI_Market_Baseline | Volume
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le dataset historique est introuvable à l'emplacement : {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Gestion de la flexibilité des noms de colonnes du dataset d'origine
    rename_mapping = {
        'Price_Close': 'Price_Close',
        'close': 'Price_Close',
        'TDI_RSI_Line': 'TDI_RSI_Line',
        'rsi_price_line': 'TDI_RSI_Line',
        'TDI_Market_Baseline': 'TDI_Market_Baseline',
        'mbl': 'TDI_Market_Baseline',
        'Volume': 'Volume',
        'volume': 'Volume'
    }
    df = df.rename(columns={k: v for k, v in rename_mapping.items() if k in df.columns})
    
    # Tri par timestamp pour garantir la chronologie
    if 'Timestamp' in df.columns:
        df = df.sort_values('Timestamp').reset_index(drop=True)
    elif 'timestamp' in df.columns:
        df = df.sort_values('timestamp').reset_index(drop=True)
        
    return df


def run_training():
    # 1. Définition des chemins d'accès
    dataset_path = "training/utils/historical_data.csv"  # Modifiez selon votre fichier réel
    model_output_dir = "models"
    log_dir = "logs"
    
    os.makedirs(model_output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    print("[MLOps] Chargement des données historiques...")
    # NOTE : Pour l'exemple, si le fichier n'existe pas encore, on génère un dataset synthétique 
    # reprenant EXACTEMENT la structure de votre exemple d'origine pour que le script tourne directement.
    if not os.path.exists(dataset_path):
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        synthetic_data = {
            "Timestamp": [1716892800, 1716892860, 1716892920, 1716892980, 1716893040] * 200,
            "Price_Close": [0.652, 0.655, 0.650, 0.648, 0.649] * 200,
            "TDI_RSI_Line": [0.580, 0.610, 0.540, 0.490, 0.510] * 200,
            "TDI_Market_Baseline": [0.510, 0.512, 0.511, 0.508, 0.507] * 200,
            "Volume": [0.450, 0.480, 0.420, 0.390, 0.410] * 200
        }
        pd.DataFrame(synthetic_data).to_csv(dataset_path, index=False)
        print(f"[MLOps] Dataset de simulation créé à : {dataset_path}")

    df = load_historical_data(dataset_path)

    # 2. Initialisation de l'environnement Gymnasium avancé
    print("[Quant] Initialisation de l'environnement de trading avec Lookback Window (10)...")
    env = AdvancedTradingEnv(df=df, initial_balance=10000.0, window_size=10)

    # 3. Configuration des Hyperparamètres PPO de niveau Production
    # Ajustés pour le trading (apprentissage stable, faible taux d'apprentissage pour éviter l'oubli catastrophique)
    ppo_hyperparameters = {
        "policy": "MlpPolicy",
        "env": env,
        "learning_rate": 3e-4,
        "n_steps": 2048,
        "batch_size": 64,
        "n_epochs": 10,
        "gamma": 0.99,          
        "gae_lambda": 0.95,
        "clip_range": 0.2,
        "ent_coef": 0.08,       # <-- AUGMENTÉ (0.01 -> 0.08) : Force l'IA à tester des trades
        "verbose": 1,
        "tensorboard_log": log_dir
    }

    print("[IA] Initialisation du modèle PPO (Stable-Baselines3)...")
    model = PPO(**ppo_hyperparameters)

    # 4. Configuration des Callbacks (Sauvegardes intermédiaires de sécurité)
    checkpoint_callback = CheckpointCallback(
        save_freq=5000, 
        save_path=model_output_dir,
        name_prefix="ppo_checkpoint"
    )
    tensorboard_callback = TensorboardCallback()

    # 5. Lancement de l'apprentissage autonome
    total_timesteps = 500000
    print(f"[IA] Début de l'entraînement pour {total_timesteps} étapes...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, tensorboard_callback],
        progress_bar=False
    )

    # 6. Exportation de l'Artefact Final (Sans l'extension .zip forcée manuellement)
    final_model_path = os.path.join(model_output_dir, "ppo_trading_policy")
    model.save(final_model_path)
    print(f"[MLOps] Entraînement terminé. Modèle de production exporté vers : {final_model_path}.zip")

if __name__ == "__main__":
    run_training()