import pandas as pd

from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


class TDIIndicator:

    def __init__(
        self,
        rsi_period=13,
        price_line_period=2,
        signal_line_period=7,
        bb_period=34,
        bb_std=1.618
    ):

        self.rsi_period = rsi_period
        self.price_line_period = price_line_period
        self.signal_line_period = signal_line_period
        self.bb_period = bb_period
        self.bb_std = bb_std

    def calculate(self, df: pd.DataFrame):

        if len(df) < 40:
            return df

        # RSI
        rsi = RSIIndicator(
            close=df["close"],
            window=self.rsi_period
        )

        df["rsi"] = rsi.rsi()

        # Price Line
        df["rsi_price_line"] = (
            df["rsi"]
            .rolling(self.price_line_period)
            .mean()
        )

        # Signal Line
        df["rsi_signal_line"] = (
            df["rsi"]
            .rolling(self.signal_line_period)
            .mean()
        )

        # Market Base Line
        df["mbl"] = (
            df["rsi"]
            .rolling(34)
            .mean()
        )

        # Bollinger Bands
        bb = BollingerBands(
            close=df["rsi"],
            window=self.bb_period,
            window_dev=self.bb_std
        )

        df["bb_upper"] = bb.bollinger_hband()
        df["bb_lower"] = bb.bollinger_lband()

        return df