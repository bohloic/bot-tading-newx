from datetime import datetime


class CandleBuilder:

    def __init__(self):

        self.current_candle = None

    def update(self, price: float, volume: float):

        now = datetime.utcnow().replace(
            second=0,
            microsecond=0
        )

        # Première bougie
        if self.current_candle is None:

            self.current_candle = {
                "time": now,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume
            }

            return None

        # Nouvelle minute = nouvelle bougie
        if now > self.current_candle["time"]:

            finished_candle = self.current_candle

            self.current_candle = {
                "time": now,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume
            }

            return finished_candle

        # Mise à jour bougie courante
        self.current_candle["high"] = max(
            self.current_candle["high"],
            price
        )

        self.current_candle["low"] = min(
            self.current_candle["low"],
            price
        )

        self.current_candle["close"] = price
        self.current_candle["volume"] += volume

        return None