import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class AdvancedTradingEnv(gym.Env):
    """
    Environnement de Trading Institutionnel pour PPO.
    Séparation stricte des données et calcul dynamique des métriques de risque.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, df: pd.DataFrame, initial_balance: float = 10000.0, window_size: int = 10):
        super(AdvancedTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.window_size = window_size
        
        # Constantes de gestion du risque
        self.risk_per_trade = 0.02  # 2%
        self.commission = 0.001     # 0.1%
        self.slippage = 0.0005      # 0.05%
        self.max_drawdown_limit = 0.30  # 30%

        # Espace des Actions : 0=HOLD, 1=BUY, 2=SELL
        self.action_space = spaces.Discrete(3)
        
        # Espace d'Observation : (window_size, 6 features)
        # Features: [close, rsi, rsi_price_line, rsi_signal_line, mbl, volume]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(self.window_size, 6), 
            dtype=np.float32
        )
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.current_step = self.window_size
        self.max_equity = self.initial_balance
        
        # État des positions : 0 = None, 1 = Long, 2 = Short
        self.position = 0
        self.entry_price = 0.0
        self.position_size = 0.0
        
        # Historique pour le calcul des performances (Sharpe/Sortino)
        self.returns_history = []
        
        return self._next_observation(), {}

    def _next_observation(self):
        # Extraction de la fenêtre glissante
        start_idx = self.current_step - self.window_size
        end_idx = self.current_step
        obs = self.df.iloc[start_idx:end_idx][[
            'Price_Close', 'TDI_RSI_Line', 'TDI_Market_Baseline', 'Volume'
        ]].copy()
        
        # Ingénierie à la volée pour compléter les 6 features demandées
        obs['rsi'] = obs['TDI_RSI_Line'] # Hypothèse de mapping direct ou calcul
        obs['rsi_signal_line'] = obs['TDI_RSI_Line'].rolling(3, min_periods=1).mean()
        
        # Conversion en float32 Numpy array
        obs_array = obs[['Price_Close', 'rsi', 'TDI_RSI_Line', 'rsi_signal_line', 'TDI_Market_Baseline', 'Volume']].to_numpy(dtype=np.float32)
        
        # Normalisation Z-score locale (évite le data leakage)
        mean = np.mean(obs_array, axis=0)
        std = np.std(obs_array, axis=0) + 1e-8
        normalized_obs = (obs_array - mean) / std
        
        return normalized_obs

    def step(self, action):
        current_price = self.df.loc[self.current_step, 'Price_Close']
        previous_equity = self.equity
        
        # execution logique de l'action
        self._execute_action(action, current_price)
        
        # Mise à jour de la valorisation du portefeuille (Equity)
        self._update_equity(current_price)
        
        # Calcul du rendement de ce step
        step_return = (self.equity - previous_equity) / (previous_equity + 1e-8)
        self.returns_history.append(step_return)
        
        # Calcul du Drawdown
        if self.equity > self.max_equity:
            self.max_equity = self.equity
        current_drawdown = (self.max_equity - self.equity) / self.max_equity
        
        # Avancement dans le dataset
        self.current_step += 1
        
        # Détermination de la fin de l'épisode (Truncated / Terminated)
        terminated = False
        truncated = self.current_step >= len(self.df) - 1
        
        if current_drawdown > self.max_drawdown_limit:
            terminated = True
        if self.equity < (self.initial_balance * 0.50):
            terminated = True
            
        # Fonction de Récompense Avancée (Quant Level)
        reward = self._calculate_reward(step_return, current_drawdown, action, terminated)
        
        obs = self._next_observation() if not (terminated or truncated) else np.zeros(self.observation_space.shape, dtype=np.float32)
        
        return obs, reward, terminated, truncated, {"equity": self.equity, "drawdown": current_drawdown}

    def _execute_action(self, action, current_price):
        # Logique simplifiée d'exécution pour l'environnement de simulation
        if action == 1 and self.position == 0:  # BUY
            self.position = 1
            self.entry_price = current_price * (1 + self.slippage)
            allocated_capital = self.balance * self.risk_per_trade
            self.position_size = allocated_capital / self.entry_price
            self.balance -= allocated_capital + (allocated_capital * self.commission)
            
        elif action == 2 and self.position == 0:  # SELL (Short)
            self.position = 2
            self.entry_price = current_price * (1 - self.slippage)
            allocated_capital = self.balance * self.risk_per_trade
            self.position_size = allocated_capital / self.entry_price
            self.balance -= allocated_capital + (allocated_capital * self.commission)
            
        elif action == 0 and self.position != 0:  # Sortie de position (HOLD forcé / TP / SL)
            if self.position == 1:  # Fermeture Long
                gross_received = self.position_size * current_price * (1 - self.slippage)
                self.balance += gross_received - (gross_received * self.commission)
            elif self.position == 2:  # Fermeture Short
                profit = (self.entry_price - current_price) * self.position_size
                gross_received = (self.position_size * self.entry_price) + profit
                self.balance += gross_received - (gross_received * self.commission)
            self.position = 0
            self.position_size = 0.0

    def _update_equity(self, current_price):
        if self.position == 1:  # Long
            self.equity = self.balance + (self.position_size * current_price)
        elif self.position == 2:  # Short
            profit = (self.entry_price - current_price) * self.position_size
            self.equity = self.balance + (self.position_size * self.entry_price) + profit
        else:
            self.equity = self.balance

    def _calculate_reward(self, step_return, drawdown, action, terminated):
        if terminated:
            return -10.0  # Pénalité majeure uniquement en cas de faillite (crash du compte)
        
        # 1. Récompense principale : Rendement géométrique net
        # On utilise le rendement de l'equity pour coller à la croissance du capital
        # Si le step est positif (gain), on amplifie la récompense pour inciter à laisser courir les gains
        if step_return > 0:
            reward = step_return * 250.0  # Amplification agressive des gains
        else:
            reward = step_return * 100.0  # Pénalité standard pour les pertes
        
        # 2. Pénalité de Drawdown quadratique (ne s'active que si le DD dépasse 5%)
        if drawdown > 0.05:
            reward -= (drawdown ** 2) * 5.0
            
        # 3. Micro-coût de friction comportemental (évite le sur-trading compulsif)
        # Mais très faible pour ne pas forcer l'agent à rester en HOLD perpétuel
        if action != 0 and self.position == 0:
            reward -= 0.001  
            
        return float(reward)