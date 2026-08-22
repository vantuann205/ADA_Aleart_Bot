import os
import re
import unittest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ["BOT_TOKEN"] = "123456:TEST_TOKEN"
os.environ["CHAT_ID"] = "1"

import bot


class AlertTests(unittest.TestCase):
    def test_no_real_telegram_token_in_source(self):
        source = Path("bot.py").read_text(encoding="utf-8")

        self.assertIsNone(re.search(r'\d{8,}:[A-Za-z0-9_-]{30,}', source))

    def test_btc_alerts_each_1000_level_crossed(self):
        alerts = bot.build_alert_messages("BTC", 1000, 100500, 102100)

        self.assertEqual([alert["level"] for alert in alerts], [101000, 102000])
        self.assertTrue(all("BTC" in alert["message"] for alert in alerts))

    def test_eth_alerts_each_100_level_crossed_down(self):
        alerts = bot.build_alert_messages("ETH", 100, 3650, 3390)

        self.assertEqual([alert["level"] for alert in alerts], [3600, 3500, 3400])
        self.assertTrue(all("ETH" in alert["message"] for alert in alerts))

    def test_failed_send_keeps_previous_price_for_retry(self):
        bot.previous_prices.clear()
        bot.previous_prices["BTC"] = 78050

        with patch.object(bot, "get_crypto_price", side_effect=[77950, 3000]), patch.object(
            bot, "send_telegram_message", return_value=False
        ):
            bot.check_price_and_alert()

        self.assertEqual(bot.previous_prices["BTC"], 78050)

    def test_delivery_check_stops_startup_when_chat_cannot_receive_messages(self):
        with patch.object(bot, "send_telegram_message_async", new=AsyncMock(return_value=False)):
            with self.assertRaisesRegex(RuntimeError, "CHAT_ID"):
                asyncio.run(bot.verify_telegram_delivery())


if __name__ == "__main__":
    unittest.main()
