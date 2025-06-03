import os
import requests
import pandas as pd
from coinbase.rest import RESTClient
from google.cloud import secretmanager
from datetime import datetime, timedelta, timezone
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Fetch credentials securely via Google Secret Manager
def get_secret(secret_name, version="latest"):
    project_id = os.getenv("GCP_PROJECT_ID")
    client = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8")

# Initialize credentials
os.environ["COINBASE_API_KEY"] = get_secret("COINBASE_API_KEY")
os.environ["COINBASE_SECRET_KEY"] = get_secret("COINBASE_SECRET_KEY")
os.environ["TELEGRAM_BOT_KEY"] = get_secret("TELEGRAM_BOT_KEY")
os.environ["TELEGRAM_CHAT_ID"] = get_secret("TELEGRAM_CHAT_ID")

# Load credentials
COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
COINBASE_SECRET_KEY = os.getenv('COINBASE_SECRET_KEY')
TELEGRAM_BOT_KEY = os.getenv('TELEGRAM_BOT_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

client = RESTClient(api_key=COINBASE_API_KEY, api_secret=COINBASE_SECRET_KEY)

MOMENTUM_COINS = ['DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'FLOKI-USD',
                  'WIF-USD', 'SOL-USD', 'RNDR-USD', 'APT-USD',
                  'OP-USD', 'COMP-USD']

def send_telegram_message(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
    try:
        response = requests.post(url, params={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        return response.ok
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return False

def fetch_candles(coin, granularity, period_hours):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=period_hours)
    response = client.get_candles(
        product_id=coin, granularity=granularity,
        start=int(start.timestamp()), end=int(end.timestamp())
    )
    return pd.DataFrame([{
        'time': pd.to_datetime(int(c['start']), unit='s'),
        'open': float(c['open']),
        'close': float(c['close']),
        'volume': float(c['volume'])
    } for c in response.candles]).sort_values('time')

def check_momentum():
    logging.info("Starting Momentum Check")
    signals = []
    for coin in MOMENTUM_COINS:
        df = fetch_candles(coin, 'ONE_DAY', 168)  # Last 7 days
        if len(df) < 2:
            continue
        yesterday = df.iloc[-2]
        avg_volume = df['volume'][:-1].mean()
        price_change = (yesterday['close'] - yesterday['open']) / yesterday['open']
        volume_change = yesterday['volume'] / avg_volume
        if price_change >= 0.10 and volume_change >= 1.5:
            msg = f"🚨 Momentum: {coin}\nPrice Change: {price_change:.2%}, Volume Spike: {volume_change:.2f}x"
            logging.info(msg)
            send_telegram_message(msg)
            signals.append(msg)
        time.sleep(1)
    summary = f"Momentum Check: {len(signals)} signals." if signals else "No Momentum signals today."
    logging.info(summary)
    send_telegram_message(summary)

def check_volume_spikes():
    logging.info("Starting Hourly Volume Spike Check")
    coins = [p['product_id'] for p in client.get_products()['products'] if p['product_id'].endswith('-USD')]
    signals = []
    for coin in coins:
        df = fetch_candles(coin, 'ONE_HOUR', 24)
        if df.empty or len(df) < 2:
            continue
        latest = df.iloc[-1]
        avg_volume = df['volume'][:-1].mean()
        price_change = (latest['close'] - latest['open']) / latest['open']
        volume_change = latest['volume'] / avg_volume
        if price_change >= 0.05 and volume_change >= 1.5:
            msg = f"🚀 Spike: {coin}\nPrice Change: {price_change:.2%}, Volume: {volume_change:.2f}x"
            logging.info(msg)
            send_telegram_message(msg)
            signals.append(msg)
        time.sleep(1)
    summary = f"Volume Spike Check: {len(signals)} signals." if signals else "No Volume spikes detected."
    logging.info(summary)
    send_telegram_message(summary)

def main():
    check_momentum()
    check_volume_spikes()

if __name__ == '__main__':
    main()
