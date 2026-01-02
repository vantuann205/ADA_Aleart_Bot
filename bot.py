import requests
import time
import schedule
import threading
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

high_alert_sent = {level: False for level in HIGH_LEVELS}
low_alert_sent = {level: False for level in LOW_LEVELS}

def get_ada_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['cardano']['usd']
    except Exception as e:
        print(f"Loi lay gia: {e}")
        return None

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
    global high_alert_sent, low_alert_sent
    
    price = get_ada_price()
    if price is None:
        return
    
    current_price = round(price, 4)
    print(f"[{time.strftime('%H:%M:%S')}] Gia ADA: ${current_price}")
    
    for level in sorted(LOW_LEVELS, reverse=True):
        if price <= level and not low_alert_sent[level]:
            message = f"ADA GIAM VE ${level}!\nGia: ${current_price}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                low_alert_sent[level] = True
                print(f"Da gui thong bao giam: ${level}")
                
                for high_level in HIGH_LEVELS:
                    high_alert_sent[high_level] = False
            return
    
    for level in sorted(HIGH_LEVELS):
        if price >= level and not high_alert_sent[level]:
            message = f"ADA TANG VUOT ${level}!\nGia: ${current_price}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                high_alert_sent[level] = True
                print(f"Da gui thong bao tang: ${level}")
                
                for low_level in LOW_LEVELS:
                    low_alert_sent[low_level] = False
            return

async def price_command(update, context):
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("Khong lay duoc gia ADA!")
        return
    
    current_price = round(price, 4)
    message = f"Gia ADA: ${current_price}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
    await update.message.reply_text(message)

async def reset_command(update, context):
    global high_alert_sent, low_alert_sent
    high_alert_sent = {level: False for level in HIGH_LEVELS}
    low_alert_sent = {level: False for level in LOW_LEVELS}
    await update.message.reply_text("Da reset! Bot se thong bao lai.")

application.add_handler(CommandHandler("price", price_command))
application.add_handler(CommandHandler("reset", reset_command))

def price_monitoring():
    print("Bat dau monitoring gia ADA...")
    check_price_and_alert()
    
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
    monitoring_thread.start()
    
    print("Bot Telegram san sang!")
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Loi chay bot: {e}")
        time.sleep(5)