"""Notification Service for Trading Alerts and Reports.

This module provides multi-channel notifications:
- Email (SMTP)
- Slack (Webhook)
- Telegram (Bot API)
- PDF Report Generation
"""
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging
from pydantic import BaseModel, Field

from app.service.daily_briefing import DailyBriefing

logger = logging.getLogger(__name__)


class EmailConfig(BaseModel):
    """Email configuration."""
    smtp_server: str = Field(..., description="SMTP server address")
    smtp_port: int = Field(default=587, description="SMTP port")
    username: str = Field(..., description="Email username")
    password: str = Field(..., description="Email password")
    from_email: str = Field(..., description="From email address")
    use_tls: bool = Field(default=True, description="Use TLS")


class SlackConfig(BaseModel):
    """Slack configuration."""
    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: Optional[str] = Field(None, description="Default channel")
    username: str = Field(default="Trading Bot", description="Bot username")


class TelegramConfig(BaseModel):
    """Telegram configuration."""
    bot_token: str = Field(..., description="Telegram bot token")
    chat_ids: List[str] = Field(..., description="Chat IDs to send messages to")


class NotificationService:
    """Multi-channel notification service."""
    
    def __init__(
        self,
        email_config: Optional[EmailConfig] = None,
        slack_config: Optional[SlackConfig] = None,
        telegram_config: Optional[TelegramConfig] = None
    ):
        """Initialize notification service.
        
        Args:
            email_config: Email configuration
            slack_config: Slack configuration
            telegram_config: Telegram configuration
        """
        self.email_config = email_config
        self.slack_config = slack_config
        self.telegram_config = telegram_config
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email notification.
        
        Args:
            to_emails: List of recipient emails
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (fallback)
            attachments: Optional list of file paths to attach
            
        Returns:
            True if sent successfully
        """
        if not self.email_config:
            logger.warning("Email config not set")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Add text version
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            
            # Add HTML version
            msg.attach(MIMEText(body_html, 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(file_path).name}'
                        )
                        msg.attach(part)
                    except Exception as e:
                        logger.error(f"Error attaching file {file_path}: {e}")
            
            # Connect and send
            if self.email_config.use_tls:
                server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.email_config.smtp_server, self.email_config.smtp_port)
            
            server.login(self.email_config.username, self.email_config.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_slack_message(
        self,
        message: str,
        channel: Optional[str] = None,
        level: str = "info",
        blocks: Optional[List[Dict]] = None
    ) -> bool:
        """Send Slack notification.
        
        Args:
            message: Message text
            channel: Channel to send to (overrides default)
            level: Message level (info, warning, error, success)
            blocks: Optional Slack blocks for rich formatting
            
        Returns:
            True if sent successfully
        """
        if not self.slack_config:
            logger.warning("Slack config not set")
            return False
        
        try:
            # Color coding by level
            color_map = {
                'info': '#3498db',
                'warning': '#f39c12',
                'error': '#e74c3c',
                'success': '#2ecc71'
            }
            
            # Construct payload
            payload = {
                'username': self.slack_config.username,
                'attachments': [{
                    'color': color_map.get(level, '#3498db'),
                    'text': message,
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            if channel or self.slack_config.channel:
                payload['channel'] = channel or self.slack_config.channel
            
            if blocks:
                payload['blocks'] = blocks
            
            # Send request
            response = requests.post(
                self.slack_config.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    def send_telegram_message(
        self,
        message: str,
        chat_ids: Optional[List[str]] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send Telegram notification.
        
        Args:
            message: Message text
            chat_ids: Chat IDs to send to (overrides default)
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            
        Returns:
            True if sent successfully to at least one chat
        """
        if not self.telegram_config:
            logger.warning("Telegram config not set")
            return False
        
        target_chats = chat_ids or self.telegram_config.chat_ids
        if not target_chats:
            logger.warning("No Telegram chat IDs configured")
            return False
        
        success_count = 0
        
        for chat_id in target_chats:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_config.bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': parse_mode
                }
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    logger.error(f"Telegram API error for chat {chat_id}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error sending Telegram message to {chat_id}: {e}")
        
        logger.info(f"Telegram messages sent to {success_count}/{len(target_chats)} chats")
        return success_count > 0
    
    def send_daily_briefing_email(
        self,
        briefing: DailyBriefing,
        to_emails: List[str]
    ) -> bool:
        """Send daily briefing via email.
        
        Args:
            briefing: DailyBriefing object
            to_emails: Recipient emails
            
        Returns:
            True if sent successfully
        """
        # Generate HTML
        html = self._generate_briefing_html(briefing)
        
        # Generate plain text fallback
        text = self._generate_briefing_text(briefing)
        
        subject = f"📊 Daily Trading Briefing: {briefing.symbol} - {briefing.recommendation_date.strftime('%Y-%m-%d')}"
        
        return self.send_email(to_emails, subject, html, text)
    
    def send_trade_alert(
        self,
        symbol: str,
        signal: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence: float,
        channels: List[str] = ["email", "slack", "telegram"]
    ) -> Dict[str, bool]:
        """Send trade alert across multiple channels.
        
        Args:
            symbol: Trading symbol
            signal: LONG or SHORT
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            confidence: Signal confidence
            channels: Channels to send to
            
        Returns:
            Dictionary of {channel: success}
        """
        results = {}
        
        # Construct message
        message = f"""
🚨 **Trade Alert: {symbol}**

📈 Signal: **{signal}**
💰 Entry: ${entry_price:,.2f}
🛑 Stop Loss: ${stop_loss:,.2f}
🎯 Take Profit: ${take_profit:,.2f}
📊 Confidence: {confidence:.1%}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # Slack
        if "slack" in channels:
            results['slack'] = self.send_slack_message(
                message,
                level="info"
            )
        
        # Telegram
        if "telegram" in channels:
            results['telegram'] = self.send_telegram_message(message)
        
        # Email
        if "email" in channels and self.email_config:
            html = f"<html><body><pre>{message}</pre></body></html>"
            # Would need to_emails parameter
            results['email'] = False  # Placeholder
        
        return results
    
    def send_risk_warning(
        self,
        warning_message: str,
        severity: str = "high"
    ) -> Dict[str, bool]:
        """Send risk warning notification.
        
        Args:
            warning_message: Warning message
            severity: Severity level (low, medium, high)
            
        Returns:
            Dictionary of {channel: success}
        """
        results = {}
        
        emoji_map = {
            'low': '⚠️',
            'medium': '🔶',
            'high': '🚨'
        }
        
        emoji = emoji_map.get(severity, '⚠️')
        
        message = f"{emoji} **Risk Warning**\n\n{warning_message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send to Slack with error level if high severity
        level = "error" if severity == "high" else "warning"
        if self.slack_config:
            results['slack'] = self.send_slack_message(message, level=level)
        
        # Send to Telegram
        if self.telegram_config:
            results['telegram'] = self.send_telegram_message(message)
        
        return results
    
    def _generate_briefing_html(self, briefing: DailyBriefing) -> str:
        """Generate HTML for daily briefing email."""
        signal_emoji = "🟢" if briefing.current_signal > 0 else ("🔴" if briefing.current_signal < 0 else "⚪")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #3498db; color: white; padding: 20px; text-align: center; }}
        .section {{ margin: 20px; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 1.2em; color: #2c3e50; }}
        .warning {{ background: #fff3cd; border-color: #ffc107; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{signal_emoji} Daily Trading Briefing</h1>
        <p>{briefing.symbol} | {briefing.recommendation_date.strftime('%Y-%m-%d')}</p>
    </div>
    
    <div class="section">
        <h2>📊 Today's Recommendation</h2>
        <p><strong>Signal:</strong> {"LONG" if briefing.current_signal > 0 else ("SHORT" if briefing.current_signal < 0 else "FLAT")}</p>
        <p><strong>Confidence:</strong> {briefing.signal_confidence:.1%}</p>
        <p><strong>Should Execute:</strong> {"✅ Yes" if briefing.should_execute else "⏸️ No"}</p>
    </div>
    
    <div class="section">
        <h2>💰 Trade Plan</h2>
        <div class="metric">
            <div class="metric-label">Entry Price</div>
            <div class="metric-value">${briefing.entry_price:,.2f if briefing.entry_price else 0}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Stop Loss</div>
            <div class="metric-value">${briefing.stop_loss:,.2f if briefing.stop_loss else 0}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Take Profit</div>
            <div class="metric-value">${briefing.take_profit:,.2f if briefing.take_profit else 0}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Performance Metrics</h2>
        <pre>{briefing.recommendation_text}</pre>
    </div>
    
    <div class="footer">
        <p>Generated by One Market Trading System</p>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>
        """
        return html
    
    def _generate_briefing_text(self, briefing: DailyBriefing) -> str:
        """Generate plain text for daily briefing email."""
        signal_str = "LONG" if briefing.current_signal > 0 else ("SHORT" if briefing.current_signal < 0 else "FLAT")
        
        text = f"""
DAILY TRADING BRIEFING
{briefing.symbol} | {briefing.recommendation_date.strftime('%Y-%m-%d')}

TODAY'S RECOMMENDATION:
- Signal: {signal_str}
- Confidence: {briefing.signal_confidence:.1%}
- Should Execute: {"Yes" if briefing.should_execute else "No"}

TRADE PLAN:
- Entry Price: ${briefing.entry_price:,.2f if briefing.entry_price else 0}
- Stop Loss: ${briefing.stop_loss:,.2f if briefing.stop_loss else 0}
- Take Profit: ${briefing.take_profit:,.2f if briefing.take_profit else 0}

PERFORMANCE METRICS:
{briefing.recommendation_text}

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        return text.strip()


