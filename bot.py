#!/usr/bin/env python3

import requests
import time
import schedule
import threading
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID_RAW = os.environ.get("CHAT_ID", "").strip()
if not BOT_TOKEN or not CHAT_ID_RAW:
    raise RuntimeError("Set BOT_TOKEN and CHAT_ID environment variables")
try:
    CHAT_ID = int(CHAT_ID_RAW)
except ValueError as exc:
    raise RuntimeError("CHAT_ID must be numeric") from exc

SYMBOLS = {
    "BTC": {"step": 1000},
    "ETH": {"step": 100},
}
CHECK_INTERVAL = 30

# Global state
bot = Bot(token=BOT_TOKEN)
previous_prices = {}
is_running = True
application = None


class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Bot is running')
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            status = "Running" if is_running else "Stopped"
            current_time = get_utc7_time()
            prices = []
            for symbol in SYMBOLS:
                price = get_crypto_price(symbol)
                prices.append(f"{symbol}: ${price:,.2f}" if price else f"{symbol}: Loading...")
            html = f"""
            <html>
            <head><title>Crypto Alert Bot</title></head>
            <body>
                <h1>🤖 Crypto Price Alert Bot</h1>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>Time (UTC+7):</strong> {current_time}</p>
                <p><strong>Current Prices:</strong> {' | '.join(prices)}</p>
                <p><strong>Alert Settings:</strong> BTC moi $1,000, ETH moi $100</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


def run_http_server():
    """Run HTTP server for health checks"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 HTTP server started on port {port}")
    server.serve_forever()


def get_crypto_price(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["amount"])
    except Exception as e:
        print(f"Loi lay gia {symbol}: {e}")
        return None


def get_utc7_time():
    utc7 = timezone(timedelta(hours=7))
    return datetime.now(utc7).strftime('%d/%m/%Y %H:%M:%S')


async def send_telegram_message_async(message):
    """Send message using async"""
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        return True
    except Exception as e:
        print(f"Loi gui tin nhan: {e}")
        return False


def send_telegram_message(message):
    """Send message from synchronous context"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(send_telegram_message_async(message))
            return result
        finally:
            loop.close()
    except Exception as e:
        print(f"Loi tao event loop: {e}")
        return False


def build_alert_messages(symbol, step, previous_price, current_price):
    prev_step = int(previous_price // step)
    curr_step = int(current_price // step)
    alerts = []

    if curr_step > prev_step:
        step_values = range(prev_step + 1, curr_step + 1)
        template = "🚀 {symbol} TANG VUOT ${level:,.0f}!\n💰 Gia hien tai: ${price:,.2f}\n🕐 {time}"
    elif curr_step < prev_step:
        step_values = range(prev_step, curr_step, -1)
        template = "🔥 {symbol} GIAM XUONG DUOI ${level:,.0f}!\n💰 Gia hien tai: ${price:,.2f}\n🕐 {time}"
    else:
        return alerts

    for step_value in step_values:
        level = step_value * step
        alerts.append({
            "level": level,
            "message": template.format(
                symbol=symbol,
                level=level,
                price=current_price,
                time=get_utc7_time(),
            ),
        })

    return alerts


def check_price_and_alert():
    for symbol, config in SYMBOLS.items():
        price = get_crypto_price(symbol)
        if price is None:
            continue

        current_price = round(price, 2)
        print(f"[{time.strftime('%H:%M:%S')}] Gia {symbol}: ${current_price:,.2f}")

        previous_price = previous_prices.get(symbol)
        if previous_price is not None:
            for alert in build_alert_messages(symbol, config["step"], previous_price, current_price):
                if not send_telegram_message(alert["message"]):
                    print(f"⚠️ Khong gui duoc thong bao {symbol}; se thu lai")
                    break
                print(f"✅ Thong bao {symbol}: ${alert['level']:,.0f}")
            else:
                previous_prices[symbol] = current_price
        else:
            previous_prices[symbol] = current_price


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = {}
    for symbol in SYMBOLS:
        price = get_crypto_price(symbol)
        if price is None:
            await update.message.reply_text(f"❌ Khong lay duoc gia {symbol}!")
            return
        prices[symbol] = price

    lines = [f"💰 Gia {symbol} hien tai: ${price:,.2f}" for symbol, price in prices.items()]
    lines.append(f"🕐 Thoi gian (UTC+7): {get_utc7_time()}")
    await update.message.reply_text("\n".join(lines))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🤖 Crypto Price Alert Bot\n\n📋 Lenh co san:\n/price - Xem gia BTC va ETH hien tai\n\n🔔 Tu dong thong bao khi BTC vuot moi $1,000 va ETH vuot moi $100"
    await update.message.reply_text(message)


def price_monitoring():
    """Price monitoring loop running in separate thread"""
    print("🚀 Starting price monitoring...")
    print("📊 Alert steps: BTC $1,000 | ETH $100")
    print(f"⏱️  Check interval: {CHECK_INTERVAL} seconds\n")

    check_price_and_alert()
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)

    # Self-ping to keep alive (every 10 minutes)
    def self_ping():
        try:
            base_url = os.environ.get('RENDER_EXTERNAL_URL')
            if not base_url:
                return
            url = f"{base_url}/health"
            requests.get(url, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] 🏓 Keep-alive ping sent to {url}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Keep-alive ping failed: {e}")

    schedule.every(10).minutes.do(self_ping)

    while is_running:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Monitoring error (will retry): {e}")
            time.sleep(5)


async def run_bot_polling():
    """Main async bot runner with polling"""
    global application

    print("🧹 Cleaning up old bot updates...")
    try:
        # Get all pending updates to clear offset - this forces Telegram to forget old connections
        updates = await bot.get_updates(offset=-1, allowed_updates=Update.ALL_TYPES, timeout=1)
        if updates:
            print(f"   Cleared {len(updates)} old updates")
    except Exception as e:
        print(f"   (cleanup note: {type(e).__name__})")

    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("start", start_command))

    print("🤖 Initializing bot...")
    await application.initialize()
    await application.start()

    monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
    monitoring_thread.start()
    print("✅ Monitoring thread started")

    print("⏳ Waiting for old connections to fully timeout (15 seconds)...")
    await asyncio.sleep(15)  # CRITICAL: give old instances maximum time to die

    print("🤖 Starting polling (only one instance allowed)...")
    print("⚠️  Make sure NO other bot instances are running!")

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries and is_running:
        try:
            # Start polling with aggressive cleanup settings
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=1.0,
                timeout=15
            )
            print("✅ Polling started successfully")

            # Keep polling until shutdown
            while is_running:
                await asyncio.sleep(1)

        except Exception as e:
            error_str = str(e)
            if "Conflict" in error_str and retry_count < max_retries - 1:
                retry_count += 1
                print(f"\n⚠️  Conflict detected (attempt {retry_count}/{max_retries})")
                print(f"   Old instance still running - waiting 20 seconds for forced disconnect...")

                # Stop current polling
                try:
                    await application.updater.stop()
                    print("   Stopped current polling")
                except Exception as stop_err:
                    print(f"   (stop error: {type(stop_err).__name__})")

                # Wait for Telegram server to timeout old connection (30 seconds)
                await asyncio.sleep(20)

                # Reset offset to clear connection state
                try:
                    await bot.get_updates(offset=-1, timeout=1)
                    print("   Reset connection state")
                except:
                    pass

                # Reinitialize application
                try:
                    await application.start()
                    print("   Reinitializing bot for retry...")
                except Exception as init_err:
                    print(f"   (init error: {type(init_err).__name__})")
            else:
                print(f"\n❌ Fatal error: {error_str}")
                raise

    # Cleanup
    try:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
    except:
        pass


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Nhan tin hieu tat bot...")
    global is_running
    is_running = False
    sys.exit(0)


def main():
    """Main entry point"""
    global is_running

    print("\n" + "="*60)
    print("🚀 Crypto Price Alert Bot Starting...")
    print("="*60)

    # Set up signal handlers
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("\n🧹 Step 1: Cleaning up any old bot instances...")
    print("   (waiting 3 seconds for Render cleanup)")
    time.sleep(3)

    # Start HTTP server thread
    print("\n🌐 Step 2: Starting HTTP server for health checks...")
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    print("✅ HTTP server started")

    print("\n🤖 Step 3: Starting Telegram bot polling...")
    try:
        # Run the async bot
        asyncio.run(run_bot_polling())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        is_running = False
        print("\n👋 Bot shutdown complete")
        print("="*60)


if __name__ == '__main__':
    main()
