import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskCheckResult:
    note: str
    is_risky: bool
    liquidity_usd: float | None
    volume_24h: float | None


def _format_usd(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


async def check_dexscreener(contract_address: str) -> RiskCheckResult:
    url = "https://api.dexscreener.com/latest/dex/search/"
    params = {"q": contract_address}

    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(url, params=params)
        if response.status_code >= 400:
            logger.warning("Dexscreener API error: %s", response.status_code)
            return RiskCheckResult(
                note="风险提示：Dexscreener API 失败，无法验证流动性",
                is_risky=True,
                liquidity_usd=None,
                volume_24h=None,
            )

        payload = response.json()

    pairs = payload.get("pairs") or []
    matched = [
        pair
        for pair in pairs
        if pair.get("chainId") == "bsc"
        and (pair.get("baseToken", {}).get("address", "").lower() == contract_address.lower())
    ]

    if not matched:
        return RiskCheckResult(
            note="风险提示：未找到 BSC 交易对，极可能无池子/假币",
            is_risky=True,
            liquidity_usd=None,
            volume_24h=None,
        )

    best = max(
        matched,
        key=lambda pair: (pair.get("liquidity", {}) or {}).get("usd", 0) or 0,
    )

    liquidity_usd = (best.get("liquidity", {}) or {}).get("usd")
    volume_24h = (best.get("volume", {}) or {}).get("h24")

    if liquidity_usd is None or liquidity_usd < 5_000:
        note = "风险提示：流动性偏低，谨慎操作"
        is_risky = True
    else:
        note = "风险提示：已检测到流动性"
        is_risky = False

    note += f" | 流动性 {_format_usd(liquidity_usd)} | 24h量 {_format_usd(volume_24h)}"

    return RiskCheckResult(
        note=note,
        is_risky=is_risky,
        liquidity_usd=liquidity_usd,
        volume_24h=volume_24h,
    )
