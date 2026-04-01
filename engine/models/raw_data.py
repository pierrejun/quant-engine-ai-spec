from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RawData:
    symbol: str
    market: str
    as_of: str
    sources: dict[str, str]
    fetched_at: str
    collection_status: dict[str, str]
    price_data: dict[str, Any] = field(default_factory=dict)
    fundamentals_data: dict[str, Any] = field(default_factory=dict)
    news_data: list[dict[str, Any]] = field(default_factory=list)
    provider_errors: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
