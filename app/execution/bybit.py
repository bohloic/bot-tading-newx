import requests

class BybitClient:

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def place_order(self, symbol, side, qty):

        url = "https://api.bybit.com/v5/order/create"

        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "qty": qty,
            "category": "linear"
        }

        headers = {
            "X-BAPI-API-KEY": self.api_key
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()