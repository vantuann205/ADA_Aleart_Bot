import requests
import time
import schedule
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import sys

print("🚀 Khoi dong bot ADA Price Alert...")

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

print(f"📊 Cau hinh: Tang {HIGH_LEVELS}, Giam {LOW_LEVELS}")

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

previous_price = None

def get_ada_price():
    try:
        print("📡 Dang lay gia ADA...")
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data['cardano']['usd']
        print(f"✅ Lay gia thanh cong: ${price}")
        return price
    except Exception as e:
        print(f"❌ Loi lay gia: {e}")
        return None

def get_utc7_time():
    utc7 = timezone(timedelta(hours=7))
    return datetime.now(utc7).strftime('%d/%m/%Y %H:%M:%S')

def send_telegram_message(message):
    try:
        print(f"📤 Dang gui tin nhan: {message[:50]}...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_msg():
            await bot.send_message(chat_id=CHAT_ID, text=message)
        
        loop.run_until_complete(send_msg())
        loop.close()
        print("✅ Gui tin nhan thanh cong!")
        return True
    except Exception as e:
        print(f"❌ Loi gui tin nhan: {e}")
        return False

def check_price_and_alert():
    global previous_price
    
    print(f"\n⏰ [{get_utc7_time()}] Kiem tra gia...")
    
    price = get_ada_price()
    if price is None:
        print("❌ Khong lay duoc gia, bo qua lan nay")
        return
    
    current_price = round(price, 4)
    print(f"💰 Gia hien tai: ${current_price}")
    
    if previous_price is not None:
        print(f"📈 Gia truoc: ${previous_price}")
        
        for level in LOW_LEVELS:
            if previous_price > level and current_price <= level:
                message = f"🔥 ADA GIAM VE ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                print(f"🚨 CANH BAO GIAM: ${level}")
                send_telegram_message(message)
        
        for level in HIGH_LEVELS:
            if previous_price < level and current_price >= level:
                message = f"🚀 ADA TANG VUOT ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                print(f"🚨 CANH BAO TANG: ${level}")
                send_telegram_message(message)
    else:
        print("ℹ️ Lan dau kiem tra, chua co gia truoc")
    
    previous_price = current_price
    print("✅ Hoan thanh kiem tra gia\n")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("� Nhan lenh: /price")
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Khong lay duoc gia ADA!")
        return
    
    current_price = round(price, 4)
    message = f"💰 Gia ADA hien tai: ${current_price}\n🕐 Thoi gian (UTC+7): {get_utc7_time()}"
    await update.message.reply_text(message)
    print("✅ Da tra loi lenh /price")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📱 Nhan lenh /start")
    message = f"🤖 ADA Price Alert Bot\n\n📋 Lenh co san:\n/price - Xem gia ADA hien tai\n\n🔔 Tu dong thong bao khi:\n🚀 Tang vuot: {HIGH_LEVELS}\n🔥 Giam ve: {LOW_LEVELS}"
    await update.message.reply_text(message)
    print("✅ Da tra loi lenh /start")

print("🔧 Dang ky command handlers...")
application.add_handler(CommandHandler("price", price_command))
application.add_handler(CommandHandler("start", start_command))
print("✅ Da dang ky commands")

def price_monitoring():
    print("🔄 Bat dau thread monitoring...")
    
    print("🧪 Test kiem tra gia lan dau...")
    check_price_and_alert()
    
    print(f"⏰ Lap lich kiem tra moi {CHECK_INTERVAL} giay...")
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    print("🔄 Vao vong lap monitoring...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"❌ Loi trong monitoring: {e}")
            time.sleep(5)

if __name__ == '__main__':
    try:
        print("🧵 Khoi dong monitoring thread...")
        monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
        monitoring_thread.start()
        print("✅ Monitoring thread da khoi dong")
        
        print("🤖 Khoi dong bot Telegram...")
        print("📡 Thu webhook truoc...")
        
        port = int(os.environ.get('PORT', 8000))
        print(f"🌐 Port: {port}")
        
        try:
            print("🔗 Dang thu webhook...")
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url="",
                url_path=""
            )
        except Exception as e:
            print(f"❌ Webhook loi: {e}")
            print("🔄 Chuyen sang polling...")
            
            try:
                application.run_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES
                )
            except Exception as e2:
                print(f"❌ Polling loi: {e2}")
                print("🔄 Chi chay monitoring...")
                
                while True:
                    try:
                        time.sleep(10)
                        print("💓 Bot van dang chay (chi monitoring)...")
                    except KeyboardInterrupt:
                        print("🛑 Dung bot")
                        break
                    except Exception as e3:
                        print(f"❌ Loi: {e3}")
                        time.sleep(5)
                        
    except Exception as e:
        print(f"❌ Loi khoi dong: {e}")
        sys.exit(1)