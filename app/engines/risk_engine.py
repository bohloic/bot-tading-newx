import logging
from typing import Dict, Any

logger = logging.getLogger("production_engine")

class RiskAndAuditEngine:
    def __init__(self, initial_capital: float = 10000.0, max_drawdown_limit: float = 0.30, risk_per_trade: float = 0.02):
        self.initial_capital = initial_capital
        self.max_drawdown_limit = max_drawdown_limit
        self.risk_per_trade = risk_per_trade
        self.kill_switch_activated = False
        self.highest_equity = initial_capital

    def process_risk_check(self, current_equity: float, proposed_action: int) -> bool:
        """
        Analyse la conformité du signal de l'IA avec les contraintes strictes de capital.
        0 = HOLD, 1 = BUY, 2 = SELL
        """
        if self.kill_switch_activated:
            logger.critical("⚠️ SIGNAL REJETÉ : Le Kill Switch de sécurité est actif !")
            return False

        # Mise à jour du pic de capital pour le calcul du Drawdown en temps réel
        if current_equity > self.highest_equity:
            self.highest_equity = current_equity

        # Calcul du Drawdown actuel
        current_drawdown = (self.highest_equity - current_equity) / self.highest_equity
        
        if current_drawdown >= self.max_drawdown_limit:
            self.trigger_kill_switch(f"Drawdown critique atteint : {current_drawdown * 100:.2f}%")
            return False

        if current_equity < (self.initial_capital * 0.50):
            self.trigger_kill_switch("Capital tombé en dessous de la limite critique de 50%.")
            return False

        # Si l'IA veut trader mais que tout est au vert, on autorise
        if proposed_action in [1, 2]:
            logger.info(f"[RISK] Signal {proposed_action} validé. Drawdown actuel: {current_drawdown * 100:.2f}%")
            return True

        return False  # HOLD ou action inconnue

    def calculate_position_size(self, current_price: float, current_balance: float) -> float:
        """Calcul dynamique de la taille de lot selon la règle des 2%."""
        risk_capital = current_balance * self.risk_per_trade
        # Calcul de la quantité d'actifs de base à acheter/vendre
        quantity = risk_capital / current_price
        return float(np.round(quantity, 4)) if 'np' in globals() else float(round(quantity, 4))

    def trigger_kill_switch(self, reason: str):
        self.kill_switch_activated = True
        logger.critical(f"🚨🚨 [KILL SWITCH ACTIVÉ] Motif : {reason}. Arrêt immédiat des opérations.")

    def audit_trade(self, order_results: Dict[str, Any]):
        """Journalisation immuable de l'ordre pour conformité et audit ultérieur."""
        logger.info(f"[AUDIT TRAIL] Ordre Exécuté avec succès - ID: {order_results.get('order_id')} | "
                    f"Sens: {order_results.get('side')} | Qté: {order_results.get('qty')} | Symbole: {order_results.get('symbol')}")