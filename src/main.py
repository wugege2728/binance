import asyncio
import json
import logging
from pathlib import Path

from config import load_config
from notifier import NotificationPayload, send_telegram_message
from parser import parse_tweet
from riskcheck import check_dexscreener
from x_stream import load_last_seen, save_last_seen, stream_tweets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bnb-meme-alert")


def load_accounts(path: str) -> list[str]:
    accounts_path = Path(path)
    payload = json.loads(accounts_path.read_text())
    accounts = payload.get("accounts") or []
    cleaned = [account.strip().lstrip("@").lower() for account in accounts if account.strip()]
    if not cleaned:
        raise RuntimeError("accounts.json is empty")
    return cleaned


def build_summary(author: str, created_at: str) -> str:
    return f"BNB MEME 推文提醒 | @{author} | {created_at}"


async def handle_stream() -> None:
    config = load_config()
    accounts = load_accounts("accounts.json")
    last_seen = load_last_seen(config.last_seen_path)

    async for tweet in stream_tweets(config.x_bearer_token, accounts, last_seen):
        parse_result = parse_tweet(tweet.text)
        risk_note = "风险提示：未检测到 CA，可能在图片或需人工判断"
        dexscreener_url = None

        if parse_result.contract_address:
            dexscreener_url = (
                "https://dexscreener.com/bsc/" + parse_result.contract_address
            )
            if config.risk_check_enabled:
                risk_result = await check_dexscreener(parse_result.contract_address)
                risk_note = risk_result.note
            else:
                risk_note = "风险提示：风控已关闭"

        summary = build_summary(tweet.author, tweet.created_at)

        payload = NotificationPayload(
            summary=summary,
            contract_address=parse_result.contract_address,
            tweet_url=tweet.tweet_url,
            dexscreener_url=dexscreener_url,
            risk_note=risk_note,
        )

        await send_telegram_message(
            token=config.tg_bot_token,
            chat_id=config.tg_chat_id,
            payload=payload,
        )

        save_last_seen(config.last_seen_path, tweet.tweet_id)
        last_seen = tweet.tweet_id


def main() -> None:
    try:
        asyncio.run(handle_stream())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")


if __name__ == "__main__":
    main()
