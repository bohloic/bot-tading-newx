import pandas as pd
import numpy as np

def generate_fake_market_data(n=5000):
    data = []

    price = 100

    for i in range(n):
        change = np.random.randn() * 0.5
        price += change

        rsi = np.random.randint(20, 80)

        data.append([
            price,
            rsi,
            rsi - 5,
            rsi + 5,
            price * 0.98,
            np.random.randint(100, 1000)
        ])

    df = pd.DataFrame(data, columns=[
        "close",
        "rsi",
        "rsi_price_line",
        "rsi_signal_line",
        "mbl",
        "volume"
    ])

    df.to_csv("market_data.csv", index=False)

    print("market_data.csv généré ✔")

generate_fake_market_data()