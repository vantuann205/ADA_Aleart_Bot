import requests
import time
import schedule
import threading
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== CẤU HÌNH Ở ĐÂY ==================
BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"
CHAT_ID = 5200218232

# Các mức giá cao (tăng đến) - báo khi giá >= mức này
HIGH_LEVELS = [0.38, 0.40, 0.45, 0.50]

# Các mức giá thấp (giảm về) - báo khi giá <= mức này  
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]

CHECK_INTERVAL = 30
# ====================================================

# Khởi tạo bot
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Theo dõi trạng thái - RESET MỖI LẦN KHỞI ĐỘNG
high_alert_sent = {level: False for level in HIGH_LEVELS}
low_alert_sent = {level: False for level in LOW_LEVELS}

def get_ada_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['cardano']['usd']
    except Exception as e:
        print(f"❌ Lỗi lấy giá: {e}")
        return None

def send_telegram_message(message):
    """Gửi tin nhắn Telegram đồng bộ"""
    try:
        # Tạo event loop mới cho thread này
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_msg():
            await bot.send_message(chat_id=CHAT_ID, text=message)
        
        loop.run_until_complete(send_msg())
        loop.close()
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn: {e}")
        return False

def check_price_and_alert():
    global high_alert_sent, low_alert_sent
    
    price = get_ada_price()
    if price is None:
        print("❌ Không lấy được giá")
        return
    
    current_price = round(price, 4)
    print(f"[{time.strftime('%H:%M:%S')}] Giá ADA: ${current_price}")
    
    # Kiểm tra mức GIẢM trước (quan trọng hơn)
    for level in sorted(LOW_LEVELS, reverse=True):
        if price <= level and not low_alert_sent[level]:
            message = f"🔥 ADA GIẢM VỀ ${level}!\n💰 Giá: ${current_price}\n🕐 {time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                low_alert_sent[level] = True
                print(f"✅ Đã gửi thông báo giảm: ${level}")
                
                # Reset tất cả mức cao khi giá giảm
                for high_level in HIGH_LEVELS:
                    high_alert_sent[high_level] = False
            return
    
    # Kiểm tra mức TĂNG
    for level in sorted(HIGH_LEVELS):
        if price >= level and not high_alert_sent[level]:
            message = f"🚀 ADA TĂNG VƯỢT ${level}!\n💰 Giá: ${current_price}\n🕐 {time.strftime('%d/%m/%Y %H:%M:%S')}"
            
            if send_telegram_message(message):
                high_alert_sent[level] = True
                print(f"✅ Đã gửi thông báo tăng: ${level}")
                
                # Reset tất cả mức thấp khi giá tăng
                for low_level in LOW_LEVELS:
                    low_alert_sent[low_level] = False
            return

# =============== COMMAND HANDLERS ===============
async def price_command(update, context):
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Không lấy được giá ADA!")
        return
    
    current_price = round(price, 4)
    message = f"💰 Giá ADA: ${current_price}\n🕐 {time.strftime('%d/%m/%Y %H:%M:%S')}"
    await update.message.reply_text(message)

async def reset_command(update, context):
    global high_alert_sent, low_alert_sent
    high_alert_sent = {level: False for level in HIGH_LEVELS}
    low_alert_sent = {level: False for level in LOW_LEVELS}
    await update.message.reply_text("✅ Đã reset! Bot sẽ thông báo lại.")

async def status_command(update, context):
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Không lấy được giá!")
        return
    
    current_price = round(price, 4)
    
    high_status = []
    for level in HIGH_LEVELS:
        status = "✅" if high_alert_sent[level] else "⏳"
        high_status.append(f"${level}: {status}")
    
    low_status = []
    for level in LOW_LEVELS:
        status = "✅" if low_alert_sent[level] else "⏳"
        low_status.append(f"${level}: {status}")
    
    message = f"📊 Giá hiện tại: ${current_price}\n\n🚀 Mức tăng:\n" + "\n".join(high_status) + "\n\n🔥 Mức giảm:\n" + "\n".join(low_status)
    await update.message.reply_text(message)

# Đăng ký commands
application.add_handler(CommandHandler("price", price_command))
application.add_handler(CommandHandler("reset", reset_command))
application.add_handler(CommandHandler("status", status_command))

def price_monitoring():
    """Thread riêng cho monitoring"""
    print("🚀 Bắt đầu monitoring giá ADA...")
    print(f"📊 Mức tăng: {HIGH_LEVELS}")
    print(f"📉 Mức giảm: {LOW_LEVELS}")
    print(f"⏰ Kiểm tra mỗi {CHECK_INTERVAL}s")
    
    # Kiểm tra ngay lần đầu
    check_price_and_alert()
    
    # Lập lịch
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Chạy monitoring trong thread riêng
    monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
    monitoring_thread.start()
    
    # Chạy bot
    print("🤖 Bot Telegram sẵn sàng!")
    print("📋 Lệnh: /price /reset /status")
    application.run_polling()