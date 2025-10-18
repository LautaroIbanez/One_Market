"""
Webhooks module for external notifications.
Supports Telegram and custom webhook URLs.
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
import structlog

from app.data.schema import Decision, Trade

logger = structlog.get_logger(__name__)


class WebhookNotifier:
    """Send notifications via webhooks."""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
    
    def send(self, payload: Dict[str, Any]) -> bool:
        """Send webhook notification."""
        try:
            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info("webhook_sent", url=self.url, status=response.status_code)
            return True
        except Exception as e:
            logger.error("webhook_failed", url=self.url, error=str(e))
            return False
    
    def notify_decision(self, decision: Decision) -> bool:
        """Send notification for new decision."""
        payload = {
            "event": "decision",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "symbol": decision.symbol,
                "timeframe": decision.timeframe,
                "direction": decision.direction,
                "entry_low": decision.entry_low,
                "entry_high": decision.entry_high,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "position_size": decision.position_size,
                "risk_pct": decision.risk_pct,
                "signal_strength": decision.signal_strength
            }
        }
        return self.send(payload)
    
    def notify_trade(self, trade: Trade) -> bool:
        """Send notification for trade execution."""
        payload = {
            "event": "trade",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "stop_loss": trade.stop_loss,
                "take_profit": trade.take_profit,
                "position_size": trade.position_size,
                "status": trade.status,
                "pnl": trade.pnl,
                "pnl_pct": trade.pnl_pct
            }
        }
        return self.send(payload)


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send Telegram message."""
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("telegram_sent", chat_id=self.chat_id)
            return True
        except Exception as e:
            logger.error("telegram_failed", error=str(e))
            return False
    
    def notify_decision(self, decision: Decision) -> bool:
        """Send Telegram notification for decision."""
        direction_emoji = "📈" if decision.direction == "long" else "📉" if decision.direction == "short" else "⏸️"
        
        message = f"""
{direction_emoji} *New Trading Signal*

*Symbol*: {decision.symbol}
*Timeframe*: {decision.timeframe}
*Direction*: {decision.direction.upper()}
*Signal Strength*: {decision.signal_strength:.1%}

*Entry Band*:
  Low: ${decision.entry_low:.2f}
  High: ${decision.entry_high:.2f}

*Stop Loss*: ${decision.stop_loss:.2f}
*Take Profit*: ${decision.take_profit:.2f}

*Position Size*: {decision.position_size:.4f}
*Risk*: {decision.risk_pct:.1%}

⏰ Valid until: {decision.meta.get('valid_until', 'N/A')}
""".strip()
        
        return self.send_message(message)
    
    def notify_trade_execution(self, trade: Trade) -> bool:
        """Send Telegram notification for trade execution."""
        message = f"""
✅ *Trade Executed*

*ID*: {trade.trade_id}
*Symbol*: {trade.symbol}
*Direction*: {trade.direction.upper()}
*Entry Price*: ${trade.entry_price:.2f}
*Position Size*: {trade.position_size:.4f}

*Stop Loss*: ${trade.stop_loss:.2f}
*Take Profit*: ${trade.take_profit:.2f}

🕐 Executed at: {trade.entry_time.strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
        
        return self.send_message(message)
    
    def notify_trade_close(self, trade: Trade) -> bool:
        """Send Telegram notification for trade close."""
        pnl_emoji = "✅" if trade.pnl > 0 else "❌" if trade.pnl < 0 else "➖"
        
        message = f"""
{pnl_emoji} *Trade Closed*

*ID*: {trade.trade_id}
*Symbol*: {trade.symbol}
*Direction*: {trade.direction.upper()}

*Entry*: ${trade.entry_price:.2f}
*Exit*: ${trade.exit_price:.2f}

*P&L*: ${trade.pnl:.2f} ({trade.pnl_pct:+.2%})
*Status*: {trade.status}

🕐 Duration: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} → {trade.exit_time.strftime('%Y-%m-%d %H:%M')}
""".strip()
        
        return self.send_message(message)
    
    def notify_daily_summary(self, metrics: Dict[str, Any]) -> bool:
        """Send daily performance summary."""
        message = f"""
📊 *Daily Summary*

*Today's Performance*:
  Trades: {metrics.get('num_trades_today', 0)}
  Win Rate: {metrics.get('win_rate_today', 0):.1%}
  P&L: ${metrics.get('pnl_today', 0):.2f}

*Overall (12 months)*:
  CAGR: {metrics.get('cagr', 0):.1%}
  Sharpe: {metrics.get('sharpe', 0):.2f}
  Max DD: {metrics.get('max_dd', 0):.1%}
  Total Trades: {metrics.get('total_trades', 0)}

📅 {datetime.now().strftime('%Y-%m-%d')}
""".strip()
        
        return self.send_message(message)


# Factory function
def create_notifier(notifier_type: str, **config) -> Optional[WebhookNotifier | TelegramNotifier]:
    """
    Create notifier instance.
    
    Args:
        notifier_type: 'webhook' or 'telegram'
        **config: Configuration parameters
    
    Returns:
        Notifier instance or None
    """
    if notifier_type == "webhook":
        url = config.get("url")
        if not url:
            logger.warning("webhook_url_missing")
            return None
        return WebhookNotifier(url, headers=config.get("headers"))
    
    elif notifier_type == "telegram":
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not bot_token or not chat_id:
            logger.warning("telegram_config_missing")
            return None
        return TelegramNotifier(bot_token, chat_id)
    
    else:
        logger.warning("unknown_notifier_type", type=notifier_type)
        return None


if __name__ == "__main__":
    # Test webhook
    print("Testing webhook notifier...")
    
    # Example decision
    from app.data.schema import Decision
    decision = Decision(
        timestamp=datetime.now(),
        symbol="BTC-USDT",
        timeframe="1h",
        direction="long",
        entry_low=40000.0,
        entry_high=40200.0,
        stop_loss=39500.0,
        take_profit=41500.0,
        position_size=0.05,
        risk_pct=0.02,
        signal_strength=0.75,
        meta={"valid_until": "12:30"}
    )
    
    # Test (will fail without real endpoint)
    webhook = WebhookNotifier("https://example.com/webhook")
    webhook.notify_decision(decision)
    
    print("Webhook test complete (check logs)")

