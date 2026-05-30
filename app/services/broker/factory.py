import os
from app.services.broker.base_broker import BaseBroker
from app.services.broker.bybit_broker import BybitBroker
from app.services.broker.exness_broker import ExnessBroker
from app.services.broker.deriv_broker import DerivBroker  # <-- LA CORRECTION EST ICI !

class BrokerFactory:
    @staticmethod
    def get_broker(market_type: str) -> BaseBroker:
        """
        Instancie dynamiquement le broker sélectionné.
        Sert de commutateur universel.
        """
        market = market_type.upper()
        
        if market == "CRYPTO":
            return BybitBroker(
                api_key=os.getenv("BYBIT_API_KEY", "mock_key"),
                api_secret=os.getenv("BYBIT_API_SECRET", "mock_secret")
            )
            
        elif market == "FOREX":
            return ExnessBroker(
                account_id=os.getenv("EXNESS_ACCOUNT", "123456"),
                password=os.getenv("EXNESS_PASSWORD", "secure_pass"),
                server=os.getenv("EXNESS_SERVER", "Exness-MT5-Real")
            )
            
        elif market == "DERIV":
            return DerivBroker(
                app_id=os.getenv("DERIV_APP_ID", "1234"),
                api_token=os.getenv("DERIV_API_TOKEN", "mock_token")
            )
            
        else:
            raise ValueError(f"Le type de marché '{market_type}' n'est pas pris en charge par l'architecture.")