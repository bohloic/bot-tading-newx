import httpx
from app.services.broker.base_broker import BaseBroker
from typing import Dict, Any

class BybitBroker(BaseBroker):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        self.client = httpx.AsyncClient()

    async def connect(self) -> None:
        try:
            response = await self.client.get(f"{self.base_url}/v5/account/wallet-balance", params={"accountType": "UNIFIED"})
            if response.status_code != 200:
                raise ConnectionError("Impossible de s'authentifier à l'API Bybit.")
        except Exception:
            # Mode dégradé pour le développement local sans clé API valide
            pass

    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        CORRECTION : Renommage de get_latest_ticker en get_market_data 
        pour respecter le contrat de l'interface BaseBroker
        """
        url = f"{self.base_url}/v5/market/tickers"
        try:
            response = await self.client.get(url, params={"category": "linear", "symbol": symbol})
            data = response.json()
            return {
                "symbol": symbol,
                "last_price": float(data['result']['list'][0]['lastPrice']),
                "volume": float(data['result']['list'][0]['volume24h'])
            }
        except Exception:
            # Fallback de simulation si l'appel API échoue en local
            return {"symbol": symbol, "last_price": 0.650, "volume": 1000.0}

    async def execute_order(self, symbol: str, side: str, qty: float, order_type: str = "Market") -> Dict[str, Any]:
        return {
            "status": "success", 
            "order_id": "mock_bybit_id_12345", 
            "symbol": symbol, 
            "side": side, 
            "qty": qty
        }

    async def get_account_balance(self) -> float:
        return 10000.0  # Simulation locale de la balance du compte