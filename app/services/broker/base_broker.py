from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseBroker(ABC):
    """
    Interface abstraite définissant les primitives obligatoires pour tout broker
    intégré à l'agent autonome.
    """
    @abstractmethod
    async def connect(self) -> None:
        """Initialise la session et valide l'authentification."""
        pass

    @abstractmethod
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Récupère le dernier prix et les volumes réels."""
        pass

    @abstractmethod
    async def execute_order(self, symbol: str, side: str, qty: float, order_type: str = "Market") -> Dict[str, Any]:
        """Envoie un ordre d'achat ou de vente au marché."""
        pass

    @abstractmethod
    async def get_account_balance(self) -> float:
        """Retourne la balance actuelle (equity disponible)."""
        pass