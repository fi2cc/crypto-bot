from coinbase.rest import RESTClient
import pandas as pd
import os
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

# Telegram details are provided via environment variables above

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, params=params)
        return response.ok
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

# Fetch available Coinbase coins
def get_coinbase_products():
    products = client.get_products()
    return [p['product_id'] for p in products['products'] if p['product_id'].endswith('-USD')]

# Fetch 24 hours of 1-hour candles
def get_hourly_data(coin):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    response = client.get_candles(
        product_id=coin,
        granularity='ONE_HOUR',
        start=int(start.timestamp()),
        end=int(end.timestamp())
    )
    candles = response.candles
    if not candles or len(candles) < 2:
        return None
    df = pd.DataFrame([{
        'time': pd.to_datetime(int(c['start']), unit='s'),
        'open': float(c['open']),
        'close': float(c['close']),
        'volume': float(c['volume'])
    } for c in candles])
    df.sort_values('time', inplace=True)
    return df

def check_hourly_spike(df):
    latest = df.iloc[-1]
    avg_volume = df['volume'][:-1].mean()
    price_change = (latest['close'] - latest['open']) / latest['open']
    volume_change = latest['volume'] / avg_volume
    return (price_change >= 0.05 and volume_change >= 1.5), price_change, volume_change

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Coinbase Volume Spike Bot started at {now}")
    coins = get_coinbase_products()
    signals_found = []
    
    for coin in coins:
        try:
            df = get_hourly_data(coin)
            if df is None:
                continue
            signal, price_chg, vol_chg = check_hourly_spike(df)
            if signal:
                msg = (f"🚀 Sudden Activity Detected!\n"
                       f"Coin: {coin}\n"
                       f"Hourly Price Change: {price_chg*100:.2f}%\n"
                       f"Volume Spike: {vol_chg*100:.2f}%\n"
                       f"Time: {now}")
                print(msg)
                send_telegram_message(msg)
                signals_found.append(msg)
            time.sleep(1)  # Rate limit management
        except Exception as e:
            print(f"Error checking {coin}: {e}")

    if not signals_found:
        no_signal_msg = f"No sudden volume spikes found at {now}."
        print(no_signal_msg)
        send_telegram_message(no_signal_msg)

if __name__ == "__main__":
    main()
