#!/bin/bash
# Railway startup script - Kill any zombie processes and start bot

# Function to kill zombie Python processes
kill_zombies() {
    echo "🧹 Checking for zombie bot processes..."
    pkill -f "python.*bot.py" 2>/dev/null || true
    sleep 2
}

# Clean environment
export PYTHONUNBUFFERED=1

# Kill any existing processes
kill_zombies

# Wait to ensure full cleanup
sleep 3

echo "🚀 Starting bot..."
exec python -u bot.py
