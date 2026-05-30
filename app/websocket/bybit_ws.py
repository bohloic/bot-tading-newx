import requests
import asyncio
import json
import websockets
import pandas as pd

from app.indicators.tdi import TDIIndicator
from app.utils.candle_builder import CandleBuilder


class BybitWebSocket:

    def __init__(self):

        self.url = "wss://stream.bybit.com/v5/public/linear"

        self.symbol = "BTCUSDT"

        self.df = pd.DataFrame(
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        self.tdi = TDIIndicator()

        self.candle_builder = CandleBuilder()

    async def connect(self):

        self.load_historical_data()

        async with websockets.connect(self.url) as websocket:

            subscribe_message = {
                "op": "subscribe",
                "args": [f"publicTrade.{self.symbol}"]
            }

            await websocket.send(
                json.dumps(subscribe_message)
            )

            print(f"Connecté à {self.symbol}")

            while True:

                message = await websocket.recv()

                data = json.loads(message)

                await self.handle_message(data)

    async def handle_message(self, data):

        if "data" not in data:
            return

        trades = data["data"]

        for trade in trades:

            price = float(trade["p"])
            volume = float(trade["v"])

            candle = self.candle_builder.update(
                price,
                volume
            )

            # Nouvelle bougie terminée
            if candle:

                self.df.loc[len(self.df)] = candle

                # Garder les 500 dernières
                self.df = self.df.tail(500)

                # Calcul TDI
                self.df = self.tdi.calculate(self.df)

                latest = self.df.iloc[-1]

                print("\n========== TDI ==========")

                print(f"Close: {latest['close']}")
                print(f"RSI: {latest.get('rsi')}")
                print(
                    f"Price Line: "
                    f"{latest.get('rsi_price_line')}"
                )

                print(
                    f"Signal Line: "
                    f"{latest.get('rsi_signal_line')}"
                )

                print(f"MBL: {latest.get('mbl')}")

    def load_historical_data(self):

        url = (
            "https://api.bybit.com/v5/market/kline"
        )

        params = {
            "category": "linear",
            "symbol": self.symbol,
            "interval": "1",
            "limit": 200
        }

        response = requests.get(url, params=params)

        data = response.json()

        candles = data["result"]["list"]

        candles.reverse()

        rows = []

        for candle in candles:

            rows.append({
                "time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            })

        self.df = pd.DataFrame(rows)

        self.df = self.tdi.calculate(self.df)

        print(
            f"Historique chargé : "
            f"{len(self.df)} bougies"
        )