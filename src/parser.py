import re
from dataclasses import dataclass

CA_REGEX = re.compile(r"0x[a-fA-F0-9]{40}")
TICKER_REGEX = re.compile(r"\$[A-Za-z0-9]{2,12}")
WORD_REGEX = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,20}")


@dataclass(frozen=True)
class ParseResult:
    contract_address: str | None
    tickers: list[str]
    keywords: list[str]
    has_ca: bool


def parse_tweet(text: str) -> ParseResult:
    contract_match = CA_REGEX.search(text)
    contract_address = contract_match.group(0) if contract_match else None

    tickers = sorted({match.group(0) for match in TICKER_REGEX.finditer(text)})
    keywords = sorted({match.group(0) for match in WORD_REGEX.finditer(text)})

    return ParseResult(
        contract_address=contract_address,
        tickers=tickers,
        keywords=keywords,
        has_ca=contract_address is not None,
    )
