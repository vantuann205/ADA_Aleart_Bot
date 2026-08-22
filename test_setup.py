#!/usr/bin/env python3
"""
Local testing script - test bot without deployment
Run this to verify everything works before deploying to Render
"""

import subprocess
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def check_python_version():
    """Check if Python 3.11+ is installed"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, you have {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} OK")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import requests
        import telegram
        import schedule
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall with: pip install -r requirements.txt")
        return False

def check_environment():
    """Check required environment variables"""
    if not os.environ.get("BOT_TOKEN") or not os.environ.get("CHAT_ID"):
        print("❌ Set BOT_TOKEN and CHAT_ID environment variables")
        return False
    print("✅ Environment variables OK")
    return True

def test_bot_import():
    """Test if bot.py can be imported without errors"""
    try:
        # Check if bot.py exists
        if not os.path.exists("bot.py"):
            print("❌ bot.py not found")
            return False

        # Try to import it
        import bot
        print("✅ bot.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing bot.py: {e}")
        return False

def test_api_connection():
    """Test if Coinbase price API is reachable"""
    try:
        import requests
        for symbol in ("BTC", "ETH"):
            response = requests.get(
                f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot",
                timeout=5
            )
            response.raise_for_status()
            price = float(response.json()["data"]["amount"])
            print(f"✅ Coinbase API OK ({symbol} price: ${price:,.2f})")
        return True
    except Exception as e:
        print(f"❌ Coinbase API error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running pre-deployment checks...\n")

    tests = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Bot import", test_bot_import),
        ("API connection", test_api_connection),
    ]

    results = []
    for name, test in tests:
        print(f"\n{name}:")
        results.append(test())

    print("\n" + "="*50)
    if all(results):
        print("✅ All checks passed! Ready for deployment.\n")
        print("📝 Next steps:")
        print("  1. Verify BOT_TOKEN and CHAT_ID in your deploy environment")
        print("  2. Test locally: python bot.py")
        print("  3. Push to GitHub")
        print("  4. Deploy on Render")
        return 0
    else:
        print("❌ Some checks failed. Fix errors above.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
