# Hướng dẫn Deploy Bot lên Fly.io để chạy liên tục

## Những thay đổi đã thực hiện:

### 1. Cấu hình Fly.io (fly.toml)
- `auto_stop_machines = 'off'` - Tắt tự động dừng máy
- `min_machines_running = 1` - Luôn có ít nhất 1 máy chạy

### 2. Thêm HTTP Server
- Bot giờ có HTTP server chạy trên port 8080
- Endpoint `/health` để Fly.io health check
- Endpoint `/` hiển thị trạng thái bot và giá ADA hiện tại

### 3. Tự động Keep-Alive
- Bot tự ping chính nó mỗi 10 phút để giữ kết nối
- Health check trong Docker để đảm bảo bot luôn chạy

## Cách deploy:

```bash
# 1. Deploy lên Fly.io
fly deploy

# 2. Kiểm tra trạng thái
fly status

# 3. Xem logs
fly logs

# 4. Kiểm tra bot có chạy không
curl https://ada-aleart-bot-yhadcq.fly.dev/health
```

## Kiểm tra bot hoạt động:

1. **Truy cập web**: https://ada-aleart-bot-yhadcq.fly.dev
2. **Health check**: https://ada-aleart-bot-yhadcq.fly.dev/health
3. **Telegram**: Gửi `/price` để kiểm tra bot

## Lưu ý:

- Bot giờ sẽ chạy liên tục 24/7
- Fly.io sẽ không tự động dừng máy nữa
- Chi phí sẽ cao hơn vì máy chạy liên tục
- Nếu muốn tiết kiệm, có thể đặt lại `auto_stop_machines = 'stop'`