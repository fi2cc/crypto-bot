import os
from coinbase.rest import RESTClient
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time

# Load credentials from environment variables
COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
COINBASE_SECRET_KEY = os.getenv('COINBASE_SECRET_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_KEY = os.getenv('TELEGRAM_BOT_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not all([
    COINBASE_API_KEY,
    COINBASE_SECRET_KEY,
    TELEGRAM_BOT_KEY,
    TELEGRAM_CHAT_ID,
]):
    raise EnvironmentError(
        "Missing required environment variables for API or Telegram credentials"
    )

client = RESTClient(api_key=COINBASE_API_KEY, api_secret=COINBASE_SECRET_KEY)

# Coins to watch for daily momentum signals
MOMENTUM_COINS = [
    'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'FLOKI-USD',
    'WIF-USD', 'SOL-USD', 'RNDR-USD', 'APT-USD',
    'OP-USD', 'COMP-USD'
]

def send_telegram_message(message: str) -> bool:
    """Send a notification to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, params=params)
        return response.ok
    except Exception as exc:
        print(f"Telegram error: {exc}")
        return False

def get_daily_data(coin: str) -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    resp = client.get_candles(
        product_id=coin,
        granularity='ONE_DAY',
        start=int(start.timestamp()),
        end=int(end.timestamp())
    )
    candles = resp.candles
    data = [{
        'date': pd.to_datetime(int(c['start']), unit='s'),
        'open': float(c['open']),
        'close': float(c['close']),
        'volume': float(c['volume'])
    } for c in candles]
    df = pd.DataFrame(data)
    df.sort_values('date', inplace=True)
    return df

def check_momentum_signal(df: pd.DataFrame):
    if len(df) < 2:
        return False, 0, 0
    yesterday = df.iloc[-2]
    avg_volume = df['volume'][:-1].mean()
    price_change = (yesterday['close'] - yesterday['open']) / yesterday['open']
    volume_change = yesterday['volume'] / avg_volume
    return (price_change >= 0.10 and volume_change >= 1.5), price_change, volume_change

def run_momentum_checks():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Momentum checks started at {now}")
    signals = []
    for coin in MOMENTUM_COINS:
        try:
            df = get_daily_data(coin)
            signal, pchg, vchg = check_momentum_signal(df)
            if signal:
                msg = (
                    f"🚨 Momentum Signal Detected!\n"
                    f"Coin: {coin}\n"
                    f"Price Change: {pchg*100:.2f}%\n"
                    f"Volume Change: {vchg*100:.2f}%\n"
                    f"Time: {now}"
                )
                print(msg)
                send_telegram_message(msg)
                signals.append(msg)
        except Exception as exc:
            print(f"Error processing {coin}: {exc}")
        time.sleep(1)

    summary = f"{len(signals)} momentum signals found at {now}." if signals else f"No momentum signals found at {now}."
    print(summary)
    send_telegram_message(summary)

def get_coinbase_products():
    products = client.get_products()
    return [p['product_id'] for p in products['products'] if p['product_id'].endswith('-USD')]

def get_hourly_data(coin: str) -> pd.DataFrame | None:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    resp = client.get_candles(
        product_id=coin,
        granularity='ONE_HOUR',
        start=int(start.timestamp()),
        end=int(end.timestamp())
    )
    candles = resp.candles
    if not candles or len(candles) < 2:
        return None
    data = [{
        'time': pd.to_datetime(int(c['start']), unit='s'),
        'open': float(c['open']),
        'close': float(c['close']),
        'volume': float(c['volume'])
    } for c in candles]
    df = pd.DataFrame(data)
    df.sort_values('time', inplace=True)
    return df

def check_hourly_spike(df: pd.DataFrame):
    latest = df.iloc[-1]
    avg_volume = df['volume'][:-1].mean()
    price_change = (latest['close'] - latest['open']) / latest['open']
    volume_change = latest['volume'] / avg_volume
    return (price_change >= 0.05 and volume_change >= 1.5), price_change, volume_change

def run_volume_spike_checks():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Volume spike checks started at {now}")
    coins = get_coinbase_products()
    signals = []
    for coin in coins:
        try:
            df = get_hourly_data(coin)
            if df is None:
                continue
            signal, pchg, vchg = check_hourly_spike(df)
            if signal:
                msg = (
                    f"🚀 Sudden Activity Detected!\n"
                    f"Coin: {coin}\n"
                    f"Hourly Price Change: {pchg*100:.2f}%\n"
                    f"Volume Spike: {vchg*100:.2f}%\n"
                    f"Time: {now}"
                )
                print(msg)
                send_telegram_message(msg)
                signals.append(msg)
            time.sleep(1)
        except Exception as exc:
            print(f"Error checking {coin}: {exc}")

    if not signals:
        msg = f"No sudden volume spikes found at {now}."
        print(msg)
        send_telegram_message(msg)


def main():
    run_momentum_checks()
    run_volume_spike_checks()

if __name__ == '__main__':
    main()
