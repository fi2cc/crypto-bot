import os
import requests

TELEGRAM_BOT_KEY = os.getenv('7957867294:AAEIHtqQjFmU2PPmbpxkw9qPCQaX0hdrgm0')
TELEGRAM_CHAT_ID = os.getenv('1581904774')

def send_test_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ Test Telegram message successful!"}
    response = requests.post(url, params=params)
    print("Telegram response:", response.json())

if __name__ == "__main__":
    send_test_message()
