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

    def test_all_requested_symbols_have_expected_steps(self):
        self.assertEqual(
            {symbol: config["step"] for symbol, config in bot.SYMBOLS.items()},
            {"BTC": 1000, "ETH": 100, "SUI": 0.1, "SOL": 1, "HYPE": 1},
        )

    def test_each_coin_alerts_one_step_up_and_down_from_anchor(self):
        anchors = {"BTC": 77546, "ETH": 2614, "SUI": 1.1, "SOL": 115.5, "HYPE": 90}

        for symbol, config in bot.SYMBOLS.items():
            anchor = anchors[symbol]
            step = config["step"]
            up = bot.build_alert_messages(symbol, step, anchor, anchor, anchor + step)
            down = bot.build_alert_messages(symbol, step, anchor, anchor, anchor - step)

            self.assertAlmostEqual(up[0]["level"], anchor + step, places=8, msg=symbol)
            self.assertAlmostEqual(down[0]["level"], anchor - step, places=8, msg=symbol)

    def test_relative_btc_alerts_use_deployment_price_as_anchor(self):
        alerts = bot.build_alert_messages("BTC", 1000, 77546, 77546, 79546)

        self.assertEqual([alert["level"] for alert in alerts], [78546, 79546])
        self.assertTrue(all("BTC" in alert["message"] for alert in alerts))

    def test_alert_messages_use_clear_vietnamese_direction_icons(self):
        up = bot.build_alert_messages("SOL", 1, 115.5, 115.5, 116.5)
        down = bot.build_alert_messages("SOL", 1, 115.5, 115.5, 114.5)

        self.assertIn("🟢⬆️", up[0]["message"])
        self.assertIn("VƯỢT QUA MỐC", up[0]["message"])
        self.assertIn("🔴⬇️", down[0]["message"])
        self.assertIn("GIẢM XUỐNG DƯỚI MỐC", down[0]["message"])

    def test_relative_solana_alerts_follow_the_user_example(self):
        up_alerts = bot.build_alert_messages("SOL", 1, 115.5, 115.5, 118.5)
        down_alerts = bot.build_alert_messages("SOL", 1, 115.5, 118.5, 112.5)

        self.assertEqual([alert["level"] for alert in up_alerts], [116.5, 117.5, 118.5])
        self.assertEqual(
            [alert["level"] for alert in down_alerts],
            [118.5, 117.5, 116.5, 114.5, 113.5, 112.5],
        )

    def test_downward_price_between_levels_does_not_skip_a_level(self):
        alerts = bot.build_alert_messages("SOL", 1, 115.5, 115.5, 114.4)

        self.assertEqual([alert["level"] for alert in alerts], [114.5])

    def test_failed_send_keeps_previous_price_for_retry(self):
        bot.price_state.clear()
        bot.price_state["BTC"] = {"anchor": 77546, "previous": 78546}

        with patch.object(bot, "get_crypto_price", side_effect=[77546, 2614, 1, 118, 90]), patch.object(
            bot, "send_telegram_message", return_value=False
        ):
            bot.check_price_and_alert()

        self.assertEqual(bot.price_state["BTC"]["previous"], 78546)

    def test_partial_delivery_advances_only_past_successful_levels(self):
        bot.price_state.clear()
        bot.price_state["SOL"] = {"anchor": 118.42, "previous": 118.42}
        prices = [84000, 2500, 1.1, 116.36, 90]
        sent = []

        with patch.object(bot, "get_crypto_price", side_effect=prices), patch.object(
            bot,
            "send_telegram_message",
            side_effect=lambda message: sent.append(message) or len(sent) == 1,
        ):
            bot.check_price_and_alert()

        self.assertEqual(len(sent), 2)
        self.assertAlmostEqual(bot.price_state["SOL"]["previous"], 117.42, places=8)

    def test_next_poll_retries_only_the_unsent_level(self):
        bot.price_state.clear()
        bot.price_state["SOL"] = {"anchor": 118.42, "previous": 118.42}
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

        self.assertIn("$117.42", sent[0])
        self.assertIn("$116.42", sent[1])
        self.assertIn("$116.42", sent[2])
        self.assertNotIn("$117.42", sent[2])
    def test_delivery_check_stops_startup_when_chat_cannot_receive_messages(self):
        with patch.object(bot, "send_telegram_message_async", new=AsyncMock(return_value=False)):
            with self.assertRaisesRegex(RuntimeError, "CHAT_ID"):
                asyncio.run(bot.verify_telegram_delivery())


if __name__ == "__main__":
    unittest.main()
