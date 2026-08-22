#!/usr/bin/env python3
"""
Troubleshooter for Render crypto alert bot
Diagnose common issues and provide solutions
"""

import subprocess
import requests
import sys
import os
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}❌{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️ {Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️ {Colors.END} {msg}")

def check_bot_token(token):
    """Verify bot token format"""
    if not token:
        print_warning("BOT_TOKEN is not set")
        return False
    if ':' not in token or len(token) < 20:
        print_error("Invalid bot token format")
        return False
    print_success("Bot token format OK")
    return True

def check_chat_id(chat_id):
    """Verify chat ID"""
    try:
        if not chat_id:
            print_warning("CHAT_ID is not set")
            return False
        if isinstance(chat_id, str):
            int(chat_id)
        print_success("Chat ID format OK")
        return True
    except ValueError:
        print_error("Chat ID must be numeric")
        return False

def check_price_api():
    """Test Coinbase price API availability"""
    try:
        for symbol in ("BTC", "ETH"):
            url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            price = float(response.json()["data"]["amount"])
            print_success(f"Coinbase API OK ({symbol}: ${price:,.2f})")
        return True
    except requests.exceptions.Timeout:
        print_error("Coinbase API timeout")
        return False
    except Exception as e:
        print_error(f"Coinbase API error: {e}")
        return False

def check_telegram_bot(token):
    """Test Telegram bot token validity"""
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print_success(f"Telegram Bot OK - @{bot_info['username']}")
                return True
            else:
                print_error("Invalid bot token")
                return False
        else:
            print_error(f"Telegram API returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Telegram API error: {e}")
        return False

def check_requirements():
    """Verify all dependencies installed"""
    required = ['requests', 'telegram', 'schedule']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print_error(f"Missing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False

    print_success("All dependencies installed")
    return True

def check_bot_file():
    """Check if bot.py is valid Python"""
    try:
        with open('bot.py', 'r') as f:
            code = f.read()
        compile(code, 'bot.py', 'exec')
        print_success("bot.py syntax OK")
        return True
    except FileNotFoundError:
        print_error("bot.py not found")
        return False
    except SyntaxError as e:
        print_error(f"bot.py syntax error: {e}")
        return False

def check_network():
    """Test network connectivity"""
    try:
        requests.get("https://google.com", timeout=3)
        print_success("Network connectivity OK")
        return True
    except:
        print_error("No internet connection or network blocked")
        return False

def main():
    print(f"\n{Colors.BLUE}🔍 Crypto Bot Troubleshooter{Colors.END}")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    bot_token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")

    # Run checks
    print("📋 Running diagnostics...\n")

    results = {
        "Network": check_network(),
        "Bot File": check_bot_file(),
        "Dependencies": check_requirements(),
        "Bot Token": check_bot_token(bot_token) if bot_token else False,
        "Chat ID": check_chat_id(chat_id) if chat_id else False,
        "Telegram API": check_telegram_bot(bot_token) if bot_token else False,
        "Coinbase API": check_price_api(),
    }

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}\n")

    if all(results.values()):
        print_success("All checks passed! ✨")
        print_info("You can deploy to Render")
        return 0
    else:
        print_warning("Some checks failed")
        print("\n🔧 Issues to fix:")
        for name, result in results.items():
            if not result:
                print(f"  • {name}")
        print("\n💡 Tips:")
        print("  1. Check BOT_TOKEN and CHAT_ID in your environment")
        print("  2. Make sure network connection is working")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Run test_setup.py for more details")
        return 1

if __name__ == '__main__':
    sys.exit(main())
