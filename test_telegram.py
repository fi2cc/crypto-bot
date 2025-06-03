import os
import requests

TELEGRAM_BOT_KEY = os.getenv('TELEGRAM_BOT_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_test_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ Test Telegram message successful!"}
    response = requests.post(url, params=params)
    print("Telegram response:", response.json())

if __name__ == "__main__":
    send_test_message()
