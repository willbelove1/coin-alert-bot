import os
import numpy as np
from .coins import fetch_price_history
import pandas as pd
import requests
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

def analyze_and_alert():
    interval = int(os.getenv("INTERVAL_MINUTES", 15))
    lookback = int(os.getenv("LOOKBACK_HOURS", 6))
    coin_ids = os.getenv("COIN_IDS", "pi-network-defi").split(",")

    for coin_id in coin_ids:
        try:
            df = fetch_price_history(coin_id, interval, lookback)
            df['MA20'] = df['price'].rolling(window=20).mean()
            df['Upper'] = df['MA20'] + 2 * df['price'].rolling(window=20).std()
            df['Lower'] = df['MA20'] - 2 * df['price'].rolling(window=20).std()
            delta = df['price'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            ema12 = df['price'].ewm(span=12, adjust=False).mean()
            ema26 = df['price'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            last = df.iloc[-1]
            alerts = []
            if last['price'] > last['Upper']: alerts.append("⚠️ *Breakout tăng*")
            if last['price'] < last['Lower']: alerts.append("⚠️ *Breakout giảm*")
            if last['RSI'] < 30: alerts.append("🔻 *RSI quá bán*")
            if last['RSI'] > 70: alerts.append("🔺 *RSI quá mua*")
            if last['MACD'] > last['Signal'] and df['MACD'].iloc[-2] <= df['Signal'].iloc[-2]:
                alerts.append("📈 *MACD cắt lên*")
            if last['MACD'] < last['Signal'] and df['MACD'].iloc[-2] >= df['Signal'].iloc[-2]:
                alerts.append("📉 *MACD cắt xuống*")

            if alerts:
                msg = f"*[{datetime.now().strftime('%H:%M')}] {coin_id.upper()} ALERT*: ${last['price']:.4f}\n" + "\n".join(alerts)
                send_alert(msg)
        except Exception as e:
            send_alert(f"❗ Lỗi {coin_id}: {str(e)}")
