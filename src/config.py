import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    x_bearer_token: str
    tg_bot_token: str
    tg_chat_id: str
    risk_check_enabled: bool
    last_seen_path: str


def _load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_config() -> Config:
    _load_env_file()

    x_bearer_token = os.getenv("X_BEARER_TOKEN", "").strip()
    tg_bot_token = os.getenv("TG_BOT_TOKEN", "").strip()
    tg_chat_id = os.getenv("TG_CHAT_ID", "").strip()
    risk_check_enabled = os.getenv("RISK_CHECK_ENABLED", "true").lower() in {"1", "true", "yes"}
    last_seen_path = os.getenv("LAST_SEEN_PATH", ".state/last_seen.json")

    missing = [
        name
        for name, value in {
            "X_BEARER_TOKEN": x_bearer_token,
            "TG_BOT_TOKEN": tg_bot_token,
            "TG_CHAT_ID": tg_chat_id,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return Config(
        x_bearer_token=x_bearer_token,
        tg_bot_token=tg_bot_token,
        tg_chat_id=tg_chat_id,
        risk_check_enabled=risk_check_enabled,
        last_seen_path=last_seen_path,
    )
