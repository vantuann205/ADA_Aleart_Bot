import requests
import time
import schedule
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

previous_price = None

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

def send_telegram_message(message):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_msg():
            await bot.send_message(chat_id=CHAT_ID, text=message)
        
        loop.run_until_complete(send_msg())
        loop.close()
        return True
    except Exception as e:
        print(f"Loi gui tin nhan: {e}")
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
                print(f"✅ Thong bao giam: ${level}")
        
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

application.add_handler(CommandHandler("price", price_command))
application.add_handler(CommandHandler("start", start_command))

def price_monitoring():
    print("🚀 Bat dau monitoring gia ADA...")
    print(f"📊 Muc tang: {HIGH_LEVELS}")
    print(f"📉 Muc giam: {LOW_LEVELS}")
    
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Loi monitoring: {e}")
            time.sleep(5)

def run_bot():
    port = int(os.environ.get('PORT', 8000))
    
    try:
        monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
        monitoring_thread.start()
        
        print(f"🤖 Bot dang chay tren port {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"https://your-app.railway.app/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    except Exception as e:
        print(f"Loi webhook, chuyen sang polling: {e}")
        try:
            application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        except Exception as e2:
            print(f"Loi polling: {e2}")
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e3:
                    print(f"Chi chay monitoring: {e3}")
                    time.sleep(5)

if __name__ == '__main__':
    run_bot()