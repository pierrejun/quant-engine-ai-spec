from __future__ import annotations

from engine.collectors.base import BaseCollector


class FundamentalsCollector(BaseCollector):
    def __init__(self, provider) -> None:
        self.provider = provider

    def collect(self, symbol: str, market: str, as_of: str) -> dict:
        return self.provider.get_fundamentals_data(symbol=symbol, market=market, as_of=as_of)
