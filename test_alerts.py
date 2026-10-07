import asyncio
import os
import re
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ["BOT_TOKEN"] = "123456:TEST_TOKEN"
os.environ["CHAT_ID"] = "1"

import bot


class AlertTests(unittest.TestCase):
    def setUp(self):
        bot.price_state.clear()

    def test_no_real_telegram_token_in_source(self):
        source = Path("bot.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\d{8,}:[A-Za-z0-9_-]{30,}", source))

    def test_all_requested_symbols_have_expected_steps(self):
        self.assertEqual(
            {symbol: config["step"] for symbol, config in bot.SYMBOLS.items()},
            {"BTC": 1000, "ETH": 100, "SUI": 0.1, "SOL": 1, "HYPE": 1},
        )

    def test_alerts_use_absolute_round_levels_for_all_coins(self):
        examples = {
            "BTC": (82900, 83100, [83000]),
            "ETH": (2490, 2510, [2500]),
            "SUI": (1.09, 1.11, [1.1]),
            "SOL": (115.4, 116.6, [116]),
            "HYPE": (87.8, 90.2, [88, 89, 90]),
        }

        for symbol, (previous, current, expected) in examples.items():
            alerts = bot.build_alert_messages(
                symbol,
                bot.SYMBOLS[symbol]["step"],
                previous,
                current,
            )
            self.assertEqual([alert["level"] for alert in alerts], expected, msg=symbol)

    def test_downward_alerts_use_absolute_round_levels(self):
        alerts = bot.build_alert_messages("BTC", 1000, 84100, 81900)
        self.assertEqual([alert["level"] for alert in alerts], [84000, 83000, 82000])

        alerts = bot.build_alert_messages("HYPE", 1, 90.2, 87.8)
        self.assertEqual([alert["level"] for alert in alerts], [90, 89, 88])

    def test_exact_level_is_not_alerted_until_price_leaves_it(self):
        self.assertEqual(bot.build_alert_messages("BTC", 1000, 82900, 83000), [])
        self.assertEqual(bot.build_alert_messages("BTC", 1000, 83100, 83000), [])
        self.assertEqual(
            [alert["level"] for alert in bot.build_alert_messages("BTC", 1000, 83000, 83100)],
            [83000],
        )
        self.assertEqual(
            [alert["level"] for alert in bot.build_alert_messages("BTC", 1000, 83000, 82900)],
            [83000],
        )
        self.assertEqual(
            [
                alert["level"]
                for alert in bot.build_alert_messages("BTC", 1000, 83000, 83001, "up")
            ],
            [83000],
        )

    def test_continuing_direction_does_not_repeat_sent_level(self):
        up = bot.build_alert_messages("SOL", 1, 116, 116.6, "up", True)
        down = bot.build_alert_messages("SOL", 1, 116, 115.4, "down", True)
        self.assertEqual([alert["level"] for alert in up], [])
        self.assertEqual([alert["level"] for alert in down], [])

    def test_alert_messages_have_vietnamese_direction_icons(self):
        up = bot.build_alert_messages("SOL", 1, 115.4, 116.6)
        down = bot.build_alert_messages("SOL", 1, 116.6, 115.4)

        self.assertIn("🟢⬆️ VƯỢT QUA MỐC $116 — SOL!", up[0]["message"])
        self.assertIn("🔴⬇️ GIẢM XUỐNG DƯỚI MỐC $116 — SOL!", down[0]["message"])
        self.assertIn("Giá hiện tại:", up[0]["message"])

    def test_failed_send_keeps_previous_price_for_retry(self):
        bot.price_state["BTC"] = {"previous": 83100, "direction": None}
        prices = [82900, 2500, 1.1, 116, 90]

        with patch.object(bot, "get_crypto_price", side_effect=prices), patch.object(
            bot, "send_telegram_message", return_value=False
        ):
            bot.check_price_and_alert()

        self.assertEqual(bot.price_state["BTC"]["previous"], 83100)

    def test_partial_delivery_advances_only_past_successful_levels(self):
        bot.price_state["SOL"] = {"previous": 118.42, "direction": None}
        prices = [84000, 2500, 1.1, 116.36, 90]
        sent = []

        with patch.object(bot, "get_crypto_price", side_effect=prices), patch.object(
            bot,
            "send_telegram_message",
            side_effect=lambda message: sent.append(message) or len(sent) == 1,
        ):
            bot.check_price_and_alert()

        self.assertEqual(len(sent), 2)
        self.assertEqual(bot.price_state["SOL"]["previous"], 118)
        self.assertEqual(bot.price_state["SOL"]["direction"], "down")
        self.assertTrue(bot.price_state["SOL"]["previous_is_alert"])

    def test_next_poll_retries_only_the_unsent_level(self):
        bot.price_state["SOL"] = {"previous": 118.42, "direction": None}
        prices = [84000, 2500, 1.1, 116.36, 90] * 2
        sent = []
        send_results = iter([True, False, True])

        with patch.object(bot, "get_crypto_price", side_effect=prices), patch.object(
            bot,
            "send_telegram_message",
            side_effect=lambda message: sent.append(message) or next(send_results),
        ):
            bot.check_price_and_alert()
            bot.check_price_and_alert()

        self.assertIn("$118", sent[0])
        self.assertIn("$117", sent[1])
        self.assertIn("$117", sent[2])
        self.assertNotIn("$118", sent[2])

    def test_delivery_check_stops_startup_when_chat_cannot_receive_messages(self):
        with patch.object(bot, "send_telegram_message_async", new=AsyncMock(return_value=False)):
            with self.assertRaisesRegex(RuntimeError, "CHAT_ID"):
                asyncio.run(bot.verify_telegram_delivery())


if __name__ == "__main__":
    unittest.main()
