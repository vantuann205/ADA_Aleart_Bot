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
    print("🚀 Starting price monitoring...")
    print(f"📊 High levels: {HIGH_LEVELS}")
    print(f"📉 Low levels: {LOW_LEVELS}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL} seconds\n")
    
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
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
                timeout=15,
                read_timeout=15
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
    print("🚀 ADA Price Alert Bot Starting...")
    print("="*60)
    
    # Set up signal handlers
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("\n🧹 Step 1: Cleaning up any old bot instances...")
    print("   (waiting 3 seconds for Railway cleanup)")
    time.sleep(3)
    
    # Start monitoring thread
    print("\n⚙️  Step 2: Starting price monitoring thread...")
    monitoring_thread = threading.Thread(target=price_monitoring, daemon=False)
    monitoring_thread.start()
    print("✅ Monitoring thread started")
    
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