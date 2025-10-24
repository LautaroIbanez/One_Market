"""Notification and alerting module.

This module provides multi-channel notifications for trading alerts and reports.
"""

from app.notifications.notification_service import (
    NotificationService,
    EmailConfig,
    SlackConfig,
    TelegramConfig
)

__all__ = [
    "NotificationService",
    "EmailConfig",
    "SlackConfig",
    "TelegramConfig"
]






