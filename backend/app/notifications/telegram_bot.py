"""
Matreshka - Telegram Bot Integration
Alerts, commands, and emergency controls via Telegram.
"""
import asyncio
from typing import Optional
import httpx
from datetime import datetime

from ..models.signal import FusedSignal, SignalDirection


class TelegramNotifier:
    """Sends trading alerts and status updates via Telegram."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.enabled = True

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured chat."""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False

    async def send_signal_alert(self, signal: FusedSignal) -> bool:
        """Format and send a fused signal alert."""
        direction_emoji = {
            SignalDirection.LONG: "\U0001f7e2",
            SignalDirection.SHORT: "\U0001f534",
            SignalDirection.NEUTRAL: "\u26aa",
        }
        emoji = direction_emoji.get(signal.direction, "\u26aa")
        agreement = f"{signal.signal_agreement*100:.0f}%"

        msg = (
            f"{emoji} <b>MATRESHKA SIGNAL</b>\n"
            f"\n"
            f"Symbol: <b>{signal.symbol}</b>\n"
            f"Direction: <b>{signal.direction.value.upper()}</b>\n"
            f"Score: <b>{signal.composite_score:+.1f}</b>\n"
            f"Confidence: <b>{signal.confidence:.0%}</b>\n"
            f"Agreement: <b>{agreement}</b> "
            f"({signal.consensus_count}v{signal.divergence_count})\n"
        )

        if signal.regime:
            msg += f"Regime: <b>{signal.regime.value}</b>\n"

        if signal.entry_price:
            msg += f"\nEntry: <code>{signal.entry_price}</code>\n"
        if signal.stop_loss:
            msg += f"SL: <code>{signal.stop_loss}</code>\n"
        if signal.take_profit:
            msg += f"TP: <code>{signal.take_profit}</code>\n"
        if signal.risk_reward_ratio:
            msg += f"R:R = <b>{signal.risk_reward_ratio:.1f}</b>\n"

        if signal.ai_comment:
            msg += f"\nAI: <i>{signal.ai_comment}</i>\n"

        # Contributing strategies
        if signal.contributing_signals:
            msg += "\nStrategies:\n"
            for s in signal.contributing_signals:
                s_emoji = "\U0001f7e2" if s.is_bullish else "\U0001f534" if s.is_bearish else "\u26aa"
                msg += f"  {s_emoji} {s.strategy_name}: {s.strength:+.0f} ({s.confidence:.0%})\n"

        msg += f"\n<i>{datetime.utcnow().strftime('%H:%M:%S UTC')}</i>"

        return await self.send_message(msg)

    async def send_trade_executed(self, symbol: str, side: str, amount: float, price: float, exchange: str) -> bool:
        msg = (
            f"\U0001f4b0 <b>TRADE EXECUTED</b>\n"
            f"\n"
            f"{symbol} | {side.upper()}\n"
            f"Amount: {amount}\n"
            f"Price: {price}\n"
            f"Exchange: {exchange}\n"
            f"<i>{datetime.utcnow().strftime('%H:%M:%S UTC')}</i>"
        )
        return await self.send_message(msg)

    async def send_error(self, error_msg: str) -> bool:
        msg = f"\u26a0 <b>MATRESHKA ERROR</b>\n\n<code>{error_msg}</code>"
        return await self.send_message(msg)
