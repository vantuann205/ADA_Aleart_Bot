import requests
import time
import schedule
import threading
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== CẤU HÌNH Ở ĐÂY ==================
BOT_TOKEN = "8053694015:AAGYuT2Dgu3LqfdFM2xurZRf7fHtsEfn8Vc"          # Thay bằng token bot thật của bạn
CHAT_ID = 5200218232                       # Chat ID của bạn (đã lấy được)

# Các mức giá cao (tăng đến) - báo khi giá >= mức này
HIGH_LEVELS = [0.38 ,0.40, 0.45, 0.50]           # Bạn có thể thêm/bớt/sửa thoải mái

# Các mức giá thấp (giảm về) - báo khi giá <= mức này
LOW_LEVELS = [0.35, 0.34, 0.33, 0.32, 0.30]  # Sắp xếp từ cao xuống thấp để dễ xử lý

CHECK_INTERVAL = 30                        # Kiểm tra mỗi 60 giây (có thể giảm xuống 30 nếu muốn nhanh hơn)
# ====================================================

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Theo dõi trạng thái từng mức để tránh gửi lặp
high_alert_sent = {level: False for level in HIGH_LEVELS}
low_alert_sent = {level: False for level in LOW_LEVELS}

def get_ada_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data['cardano']['usd']
    except Exception as e:
        print(f"Lỗi lấy giá: {e}")
        return None

# Command handlers
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /price để lấy giá ADA hiện tại"""
    price = get_ada_price()
    if price is None:
        await update.message.reply_text("❌ Không thể lấy giá ADA hiện tại. Vui lòng thử lại sau!")
        return
    
    current_price = round(price, 4)
    message = f"💰 **Giá ADA hiện tại**\n" \
              f"💵 ${current_price}\n" \
              f"🕐 Thời gian: {time.strftime('%d/%m/%Y %H:%M:%S')}"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    message = f"🤖 **Chào mừng đến với ADA Price Bot!**\n\n" \
              f"📋 **Các lệnh có sẵn:**\n" \
              f"/price - Xem giá ADA hiện tại\n" \
              f"/start - Hiển thị menu này\n\n" \
              f"🔔 Bot sẽ tự động thông báo khi:\n" \
              f"🚀 Giá tăng vượt: {HIGH_LEVELS}\n" \
              f"🔥 Giá giảm về: {LOW_LEVELS}"
    
    await update.message.reply_text(message, parse_mode='Markdown')

def check_price_and_alert():
    global high_alert_sent, low_alert_sent
    
    price = get_ada_price()
    if price is None:
        return
    
    current_price = round(price, 4)
    print(f"[{time.strftime('%H:%M:%S')}] Giá ADA hiện tại: ${current_price}")

    message = None

    # Kiểm tra các mức cao (tăng đến)
    for level in sorted(HIGH_LEVELS):
        if price >= level and not high_alert_sent[level]:
            message = f"🚀 ADA ĐÃ TĂNG VƯỢT MỨC ${level}!\n" \
                      f"Giá hiện tại: ${current_price}\n" \
                      f"Thời gian: {time.strftime('%d/%m/%Y %H:%M:%S')}"
            high_alert_sent[level] = True
            # Reset các mức thấp nếu giá đang tăng mạnh
            for low_level in LOW_LEVELS:
                low_alert_sent[low_level] = False
            break  # Chỉ gửi 1 thông báo cho mức cao nhất đạt được

    # Kiểm tra các mức thấp (giảm về)
    if not message:  # Chỉ kiểm tra mức thấp nếu chưa gửi báo cáo tăng
        for level in sorted(LOW_LEVELS, reverse=True):  # Từ cao xuống thấp
            if price <= level and not low_alert_sent[level]:
                message = f"🔥 ADA ĐÃ GIẢM VỀ MỨC ${level}!\n" \
                          f"Giá hiện tại: ${current_price}\n" \
                          f"Thời gian: {time.strftime('%d/%m/%Y %H:%M:%S')}"
                low_alert_sent[level] = True
                # Reset các mức cao nếu giá đang giảm
                for high_level in HIGH_LEVELS:
                    high_alert_sent[high_level] = False
                break  # Chỉ gửi 1 thông báo cho mức thấp nhất đạt được

    if message:
        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print("✅ Đã gửi thông báo Telegram!")
        except Exception as e:
            print(f"Lỗi gửi tin nhắn: {e}")

# Thêm command handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("price", price_command))

def price_monitoring():
    """Chạy monitoring giá trong thread riêng"""
    print("Bot đang khởi động...")
    check_price_and_alert()
    
    print(f"Bot đang chạy! Theo dõi giá ADA mỗi {CHECK_INTERVAL} giây...")
    print(f"Mức cao báo tăng: {HIGH_LEVELS}")
    print(f"Mức thấp báo giảm: {LOW_LEVELS}")
    
    # Lập lịch kiểm tra định kỳ
    schedule.every(CHECK_INTERVAL).seconds.do(check_price_and_alert)
    
    # Vòng lặp monitoring
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Chạy price monitoring trong thread riêng
    monitoring_thread = threading.Thread(target=price_monitoring, daemon=True)
    monitoring_thread.start()
    
    # Chạy bot commands
    print("🤖 Bot Telegram đã sẵn sàng!")
    print("📋 Các lệnh có sẵn: /start, /price")
    application.run_polling()