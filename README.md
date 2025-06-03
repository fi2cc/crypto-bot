# Crypto Alert Bot

This repository contains a single script, `src/crypto_alert_bot.py`, which combines the previous momentum and volume‑spike bots into one tool. The bot checks for:

1. **Daily momentum signals** on a predefined set of coins.
2. **Hourly volume spikes** across all Coinbase USD pairs.

Notifications are sent to a Telegram chat when signals occur.

## Getting Started

Clone the project from GitHub and install dependencies:

```bash
git clone https://github.com/fi2cc/crypto-bot.git
cd crypto-bot
pip install pandas requests coinbase
```

## Setup

The bot expects credentials in environment variables:

- `COINBASE_API_KEY` – Coinbase API key name
- `COINBASE_SECRET_KEY` – Coinbase private key
- `TELEGRAM_BOT_KEY` – Telegram bot token
- `TELEGRAM_CHAT_ID` – Telegram chat ID
- `OPENAI_API_KEY` – OpenAI API key (currently unused)

Set these variables before running the script. Credentials are no longer loaded
from `cdp_api_key.json` for security reasons.

## Usage

```bash
python3 src/crypto_alert_bot.py
```

The script runs both checks sequentially and sends summaries to Telegram.
