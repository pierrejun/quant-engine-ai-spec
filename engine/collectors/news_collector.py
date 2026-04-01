from __future__ import annotations

from engine.collectors.base import BaseCollector


class NewsCollector(BaseCollector):
    def __init__(self, provider) -> None:
        self.provider = provider

    def collect(self, symbol: str, market: str, as_of: str) -> list[dict]:
        return self.provider.get_news_data(symbol=symbol, market=market, as_of=as_of)
