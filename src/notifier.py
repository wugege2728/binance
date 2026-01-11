import html
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationPayload:
    summary: str
    contract_address: str | None
    tweet_url: str
    dexscreener_url: str | None
    risk_note: str


def build_message(payload: NotificationPayload) -> str:
    summary = html.escape(payload.summary)
    ca_line = html.escape(payload.contract_address or "NO_CA")
    tweet_link = html.escape(payload.tweet_url)

    lines = [
        summary,
        ca_line,
        f"<a href=\"{tweet_link}\">Tweet Link</a>",
    ]

    if payload.dexscreener_url:
        dex_link = html.escape(payload.dexscreener_url)
        lines.append(f"<a href=\"{dex_link}\">Dexscreener</a>")

    lines.append(html.escape(payload.risk_note))
    return "\n".join(lines)


async def send_telegram_message(token: str, chat_id: str, payload: NotificationPayload) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message = build_message(payload)

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, data=data)
        if response.status_code >= 400:
            logger.warning("Telegram send failed with status %s", response.status_code)
