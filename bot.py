import requests
import time
import schedule
import asyncio
from telegram import Bot

BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]
CHECK_INTERVAL = 30

bot = Bot(token=BOT_TOKEN)

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
        print("Da gui thong bao thanh cong!")
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
            message = f"🔥 ADA GIAM VE ${level}!\n💰 Gia: ${current_price}\n🕐 {time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                low_alert_sent[level] = True
                print(f"✅ Thong bao giam: ${level}")
                
                for high_level in HIGH_LEVELS:
                    high_alert_sent[high_level] = False
            return
    
    for level in sorted(HIGH_LEVELS):
        if price >= level and not high_alert_sent[level]:
            message = f"🚀 ADA TANG VUOT ${level}!\n💰 Gia: ${current_price}\n🕐 {time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                high_alert_sent[level] = True
                print(f"✅ Thong bao tang: ${level}")
                
                for low_level in LOW_LEVELS:
                    low_alert_sent[low_level] = False
            return

if __name__ == '__main__':
    print("🚀 Bot ADA Price Alert dang khoi dong...")
    print(f"📊 Muc tang: {HIGH_LEVELS}")
    print(f"📉 Muc giam: {LOW_LEVELS}")
    print(f"⏰ Kiem tra moi {CHECK_INTERVAL}s")
    
    check_price_and_alert()
    
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    print("✅ Bot dang chay va theo doi gia ADA...")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Bot dung hoat dong!")
            break
        except Exception as e:
            print(f"Loi: {e}")
            time.sleep(5)