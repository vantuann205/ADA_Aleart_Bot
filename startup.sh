#!/bin/bash

echo "🚀 Starting ADA Alert Bot..."

# Kill any existing Python processes (cleanup)
pkill -f python3 2>/dev/null || true
pkill -f bot.py 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "🐍 Starting Python bot..."

# Start the bot with proper error handling
exec python3 -u bot.py