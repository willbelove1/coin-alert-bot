import os
import time
import pandas as pd
import requests

def fetch_price_history(coin_id, interval, lookback_hours):
    end = int(time.time())
    start = end - lookback_hours * 3600
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range?vs_currency=usd&from={start}&to={end}"
    data = requests.get(url).json()

    prices = data.get("prices", [])
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.resample(f"{interval}min").last().dropna()
    return df
