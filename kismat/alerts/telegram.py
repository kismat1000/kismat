"""Telegram alerts. Free. No-op when the bot token or chat id is missing."""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)


def send(text: str, token: str, chat_id: str, timeout: int = 15) -> bool:
    if not token or not chat_id:
        log.info("telegram not configured; message:\n%s", text)
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True},
                          timeout=timeout)
        r.raise_for_status()
        return True
    except Exception as exc:
        log.warning("telegram send failed: %s", exc)
        return False
