import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RULES_URL = "https://api.twitter.com/2/tweets/search/stream/rules"
STREAM_URL = "https://api.twitter.com/2/tweets/search/stream"


@dataclass(frozen=True)
class Tweet:
    tweet_id: int
    author: str
    created_at: str
    text: str
    tweet_url: str


def _auth_headers(bearer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {bearer_token}"}


def load_last_seen(path: str) -> int:
    file_path = Path(path)
    if not file_path.exists():
        return 0
    try:
        payload = json.loads(file_path.read_text())
        return int(payload.get("last_seen", 0))
    except (ValueError, json.JSONDecodeError):
        return 0


def save_last_seen(path: str, tweet_id: int) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps({"last_seen": tweet_id}))


def build_rule(accounts: list[str]) -> str:
    accounts_query = " OR ".join(f"from:{account}" for account in accounts)
    return f"({accounts_query}) -is:retweet -is:reply"


async def sync_rules(bearer_token: str, accounts: list[str]) -> None:
    headers = _auth_headers(bearer_token)
    async with httpx.AsyncClient(timeout=10) as client:
        existing = await client.get(RULES_URL, headers=headers)
        existing.raise_for_status()
        existing_rules = existing.json().get("data") or []

        if existing_rules:
            ids = [rule["id"] for rule in existing_rules]
            await client.post(RULES_URL, headers=headers, json={"delete": {"ids": ids}})

        rule_value = build_rule(accounts)
        response = await client.post(
            RULES_URL,
            headers=headers,
            json={"add": [{"value": rule_value, "tag": "meme-watch"}]},
        )
        response.raise_for_status()


async def stream_tweets(bearer_token: str, accounts: list[str], last_seen: int):
    await sync_rules(bearer_token, accounts)

    backoff = 1
    headers = _auth_headers(bearer_token)
    params = {
        "tweet.fields": "created_at,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }

    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", STREAM_URL, headers=headers, params=params) as response:
                    response.raise_for_status()
                    backoff = 1
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        payload = json.loads(line)
                        if "data" not in payload:
                            continue

                        tweet_data = payload["data"]
                        tweet_id = int(tweet_data["id"])
                        if tweet_id <= last_seen:
                            continue

                        includes = payload.get("includes", {})
                        users = {user["id"]: user["username"] for user in includes.get("users", [])}
                        author_username = users.get(tweet_data.get("author_id"), "unknown")

                        tweet = Tweet(
                            tweet_id=tweet_id,
                            author=author_username,
                            created_at=tweet_data.get("created_at", ""),
                            text=tweet_data.get("text", ""),
                            tweet_url=f"https://x.com/{author_username}/status/{tweet_id}",
                        )

                        last_seen = tweet_id
                        yield tweet
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.warning("Stream error: %s. Reconnecting in %s seconds.", exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
