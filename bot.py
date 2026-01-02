#!/usr/bin/env python3

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

# Flush output ngay lập tức
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("🚀 KHOI DONG BOT ADA PRICE ALERT...", flush=True)

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

print(f"📊 CAU HINH: Tang {HIGH_LEVELS}, Giam {LOW_LEVELS}", flush=True)

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

previous_price = None

def get_ada_price():
    try:
        print("📡 DANG LAY GIA ADA...", flush=True)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data['cardano']['usd']
        print(f"✅ LAY GIA THANH CONG: ${price}", flush=True)
        return price
    except Exception as e:
        print(f"❌ LOI LAY GIA: {e}", flush=True)
        return None

def get_utc7_time():
    utc7 = timezone(timedelta(hours=7))
    return datetime.now(utc7).strftime('%d/%m/%Y %H:%M:%S')

def send_telegram_message(message):
    try:
        print(f"📤 DANG GUI TIN NHAN: {message[:50]}...", flush=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_msg():
            await bot.send_message(chat_id=CHAT_ID, text=message)
        
        loop.run_until_complete(send_msg())
        loop.close()
        print("✅ GUI TIN NHAN THANH CONG!", flush=True)
        return True
    except Exception as e:
        print(f"❌ LOI GUI TIN NHAN: {e}", flush=True)
        return False

def check_price_and_alert():
    global previous_price
    
    print(f"\n⏰ [{get_utc7_time()}] KIEM TRA GIA...", flush=True)
    
    price = get_ada_price()
    if price is None:
        print("❌ KHONG LAY DUOC GIA, BO QUA LAN NAY", flush=True)
        return
    
    current_price = round(price, 4)
    print(f"💰 GIA HIEN TAI: ${current_price}", flush=True)
    
    if previous_price is not None:
        print(f"📈 GIA TRUOC: ${previous_price}", flush=True)
        
        for level in LOW_LEVELS:
            if previous_price > level and current_price <= level:
                message = f"� ADDA GIAM VE ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                print(f"🚨 CANH BAO GIAM: ${level}", flush=True)
                send_telegram_message(message)
        
        for level in HIGH_LEVELS:
            if previous_price < level and current_price >= level:
                message = f"🚀 ADA TANG VUOT ${level}!\n💰 Gia: ${current_price}\n🕐 {get_utc7_time()}"
                print(f"🚨 CANH BAO TANG: ${level}", flush=True)
                send_telegram_message(message)
    else:
        print("ℹ️ LAN DAU KIEM TRA, CHUA CO GIA TRUOC", flush=True)
    
    previous_price = current_price
    print("✅ HOAN THANH KIEM TRA GIA\n", flush=True)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📱 NHAN LENH /price", flush=True)
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Khong lay duoc gia ADA!")
        return
    
    current_price = round(price, 4)
    message = f"💰 Gia ADA hien tai: ${current_price}\n🕐 Thoi gian (UTC+7): {get_utc7_time()}"
    await update.message.reply_text(message)
    print("✅ DA TRA LOI LENH /price", flush=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📱 NHAN LENH /start", flush=True)
    message = f"🤖 ADA Price Alert Bot\n\n📋 Lenh co san:\n/price - Xem gia ADA hien tai\n\n🔔 Tu dong thong bao khi:\n🚀 Tang vuot: {HIGH_LEVELS}\n🔥 Giam ve: {LOW_LEVELS}"
    await update.message.reply_text(message)
    print("✅ DA TRA LOI LENH /start", flush=True)

print("� DANG KY  COMMAND HANDLERS...", flush=True)
application.add_handler(CommandHandler("price", price_command))
application.add_handler(CommandHandler("start", start_command))
print("✅ DA DANG KY COMMANDS", flush=True)

def price_monitoring():
    print("🔄 BAT DAU THREAD MONITORING...", flush=True)
    
    print("🧪 TEST KIEM TRA GIA LAN DAU...", flush=True)
    check_price_and_alert()
    
    print(f"⏰ LAP LICH KIEM TRA MOI {CHECK_INTERVAL} GIAY...", flush=True)
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    print("🔄 VAO VONG LAP MONITORING...", flush=True)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"❌ LOI TRONG MONITORING: {e}", flush=True)
            time.sleep(5)

if __name__ == '__main__':
    try:
        print("🧵 KHOI DONG MONITORING THREAD...", flush=True)
        monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
        monitoring_thread.start()
        print("✅ MONITORING THREAD DA KHOI DONG", flush=True)
        
        print("🤖 KHOI DONG BOT TELEGRAM...", flush=True)
        
        port = int(os.environ.get('PORT', 8000))
        print(f"🌐 PORT: {port}", flush=True)
        
        print("🔄 CHI CHAY MONITORING (KHONG DUNG WEBHOOK/POLLING)...", flush=True)
        
        # Chỉ chạy monitoring, không dùng webhook/polling để tránh lỗi
        while True:
            try:
                time.sleep(10)
                print("💓 BOT VAN DANG CHAY...", flush=True)
            except KeyboardInterrupt:
                print("🛑 DUNG BOT", flush=True)
                break
            except Exception as e:
                print(f"❌ LOI: {e}", flush=True)
                time.sleep(5)
                        
    except Exception as e:
        print(f"❌ LOI KHOI DONG: {e}", flush=True)
        sys.exit(1)