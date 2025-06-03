from coinbase.rest import RESTClient
import pandas as pd
import numpy as np
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

# Momentum coins on Coinbase
coins = ['DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'FLOKI-USD', 
         'WIF-USD', 'SOL-USD', 'RNDR-USD', 'APT-USD', 
         'OP-USD', 'COMP-USD']

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

def get_daily_data(coin):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    response = client.get_candles(
        product_id=coin,
        granularity='ONE_DAY',
        start=int(start.timestamp()),
        end=int(end.timestamp())
    )
    candles = response.candles
    df = pd.DataFrame([{
        'date': pd.to_datetime(int(c['start']), unit='s'),
        'open': float(c['open']),
        'close': float(c['close']),
        'volume': float(c['volume'])
    } for c in candles])
    df.sort_values('date', inplace=True)
    return df

def check_signal(df):
    if len(df) < 2:
        return False, 0, 0
    yesterday = df.iloc[-2]
    avg_volume = df['volume'][:-1].mean()
    price_change = (yesterday['close'] - yesterday['open']) / yesterday['open']
    volume_change = yesterday['volume'] / avg_volume
    return (price_change >= 0.10 and volume_change >= 1.5), price_change, volume_change

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Bot started at {now}")
    signals_found = []
    with open("advanced_momentum_log.txt", "a") as log:
        log.write(f"\nBot Run at {now}\n")
        for coin in coins:
            try:
                print(f"Checking {coin}...")
                df = get_daily_data(coin)
                signal, price_chg, vol_chg = check_signal(df)
                if signal:
                    msg = (f"🚨 Momentum Signal Detected!\n"
                           f"Coin: {coin}\n"
                           f"Price Change: {price_chg*100:.2f}%\n"
                           f"Volume Change: {vol_chg*100:.2f}%\n"
                           f"Time: {now}")
                    print(msg)
                    log.write(msg + '\n')
                    sent = send_telegram_message(msg)
                    if sent:
                        print("Telegram notification sent successfully.")
                    else:
                        print("Failed to send Telegram notification.")
                    signals_found.append(msg)
                else:
                    no_signal_msg = f"No momentum for {coin} at {now}."
                    print(no_signal_msg)
                    log.write(no_signal_msg + '\n')
            except Exception as e:
                error_msg = f"Error processing {coin} at {now}: {e}"
                print(error_msg)
                log.write(error_msg + '\n')
            time.sleep(1)  # avoid API rate limits

        if signals_found:
            summary_msg = f"{len(signals_found)} momentum signals found at {now}."
        else:
            summary_msg = f"No momentum signals found at {now}."
        
        print(summary_msg)
        log.write(summary_msg + '\n')

        # Send summary via Telegram for every run explicitly
        send_telegram_message(summary_msg)

if __name__ == "__main__":
    main()
