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
import os

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

# Global state
bot = Bot(token=BOT_TOKEN)
previous_price = None
is_running = True
application = None


def get_ada_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['cardano']['usd']
    except Exception as e:
        print(f"Loi lay gia: {e}")
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


def check_price_and_alert():
    global previous_price
    
    price = get_ada_price()
    if price is None:
        return
    
    current_price = round(price, 4)
    print(f"[{time.strftime('%H:%M:%S')}] Gia ADA: ${current_price}")
    
    if previous_price is not None:
        for level in LOW_LEVELS:
            if previous_price > level and current_price <= level:
                message = f"🔥 ADA GIAM VE ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                send_telegram_message(message)
        
        for level in HIGH_LEVELS:
            if previous_price < level and current_price >= level:
                message = f"🚀 ADA TANG VUOT ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                send_telegram_message(message)
                print(f"✅ Thong bao tang: ${level}")
    
    previous_price = current_price


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Khong lay duoc gia ADA!")
        return
    
    current_price = round(price, 4)
    message = f"💰 Gia ADA hien tai: ${current_price}\n🕐 Thoi gian (UTC+7): {get_utc7_time()}"
    await update.message.reply_text(message)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = f"🤖 ADA Price Alert Bot\n\n📋 Lenh co san:\n/price - Xem gia ADA hien tai\n\n🔔 Tu dong thong bao khi:\n🚀 Tang vuot: {HIGH_LEVELS}\n🔥 Giam ve: {LOW_LEVELS}"
    await update.message.reply_text(message)


def price_monitoring():
    """Price monitoring loop running in separate thread"""
    print("🚀 Bat dau monitoring gia ADA...")
    print(f"📊 Muc tang: {HIGH_LEVELS}")
    print(f"📉 Muc giam: {LOW_LEVELS}")
    
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    while is_running:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Loi monitoring: {e}")
            time.sleep(5)


async def run_bot_polling():
    """Main async bot runner with polling"""
    global application
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("start", start_command))
    
    print("🤖 Initializing bot...")
    await application.initialize()
    await application.start()
    
    print("🤖 Starting polling (only one instance allowed)...")
    print("⚠️  Make sure NO other bot instances are running!")
    
    try:
        # This is the key: use proper polling with drop_pending_updates
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        print("✅ Polling started successfully")
        
        # Keep polling until shutdown
        while is_running:
            await asyncio.sleep(1)
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Nhan tin hieu tat bot...")
    global is_running
    is_running = False
    sys.exit(0)


def main():
    """Main entry point"""
    global is_running
    
    # Set up signal handlers
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=price_monitoring, daemon=False)
    monitoring_thread.start()
    print("✅ Monitoring thread started")
    
    try:
        # Run the async bot
        asyncio.run(run_bot_polling())
    except KeyboardInterrupt:
        print("\n🛑 Bot dung lai")
    except Exception as e:
        print(f"❌ Loi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        is_running = False
        print("👋 Bot tat")


if __name__ == '__main__':
    main()