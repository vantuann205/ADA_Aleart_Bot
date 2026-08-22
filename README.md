# Crypto Telegram Alert Bot

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=black)](https://render.com/)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey)](#license)

A lightweight Telegram bot that monitors BTC and ETH spot prices and sends alerts when price levels are crossed.

## Alerts

- BTC: sends an alert every time price crosses a 1,000 USD level.
- ETH: sends an alert every time price crosses a 100 USD level.
- Both upward and downward crossings are supported.

## Requirements

- Python 3.11+
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram chat ID for the alert recipient
- Render Web Service or Docker deployment

## Environment Variables

Set these variables in Render:

| Key | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram bot token from `@BotFather`. |
| `CHAT_ID` | Yes | Telegram chat ID that receives alerts. |
| `PORT` | No | HTTP health server port. Defaults to `10000`. |

Never commit `.env` files or real tokens to git.

## Deploy on Render

### Docker Service

Render can deploy this repository directly from the included `Dockerfile`.

Recommended settings:

```text
Environment: Docker
Health Check Path: /health
```

### Python Service

If you deploy without Docker, use:

```text
Build Command: pip install -r requirements.txt
Start Command: python -u bot.py
Health Check Path: /health
```

## How to Set Environment Variables on Render

1. Open your Render dashboard.
2. Select the bot service.
3. Open the **Environment** tab.
4. Click **Add Environment Variable**.
5. Add `BOT_TOKEN` and `CHAT_ID`.
6. Save changes and redeploy the service if Render does not redeploy automatically.

Render provides `RENDER_EXTERNAL_URL` for web services. The bot uses it for the optional self health ping.

## Local Validation

Use temporary environment variables before importing or running the bot:

```bash
set BOT_TOKEN=123456:TEST_TOKEN
set CHAT_ID=1
python test_setup.py
python -m unittest test_alerts.py
```

PowerShell:

```powershell
$env:BOT_TOKEN="123456:TEST_TOKEN"
$env:CHAT_ID="1"
python test_setup.py
python -m unittest test_alerts.py
```

## Security Notes

- If a Telegram token was ever committed to git, treat it as compromised.
- Rotate the bot token in `@BotFather`.
- Store the new token only in Render environment variables.
- Do not print secrets in logs.

## License

Proprietary. All rights reserved.

Copyright (c) 2026 @Tuanngo.
