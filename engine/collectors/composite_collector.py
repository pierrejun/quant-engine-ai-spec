from __future__ import annotations

from engine.common import utc_now_iso
from engine.exceptions import CollectionError, ProviderError
from engine.models.raw_data import RawData


class CompositeCollector:
    def __init__(self, price_collector, fundamentals_collector, news_collector) -> None:
        self.price_collector = price_collector
        self.fundamentals_collector = fundamentals_collector
        self.news_collector = news_collector

    def collect(self, symbol: str, market: str, as_of: str) -> dict:
        sources = {}
        statuses = {}
        errors: list[str] = []
        price_data: dict = {}
        fundamentals_data: dict = {}
        news_data: list[dict] = []

        try:
            price_data = self.price_collector.collect(symbol, market, as_of)
            sources["price"] = price_data.get("source", "unknown")
            statuses["price"] = "ok"
        except ProviderError as exc:
            errors.append(f"price:{exc}")
            statuses["price"] = "error"

        try:
            fundamentals_data = self.fundamentals_collector.collect(symbol, market, as_of)
            sources["fundamentals"] = fundamentals_data.get("source", "unknown")
            statuses["fundamentals"] = "ok"
        except ProviderError as exc:
            errors.append(f"fundamentals:{exc}")
            statuses["fundamentals"] = "error"

        try:
            news_data = self.news_collector.collect(symbol, market, as_of)
            sources["news"] = news_data[0].get("source", "unknown") if news_data else "unknown"
            statuses["news"] = "ok" if news_data else "partial"
        except ProviderError as exc:
            errors.append(f"news:{exc}")
            statuses["news"] = "error"

        if statuses.get("price") == "error":
            raise CollectionError("price collection is required for analysis")

        raw = RawData(
            symbol=symbol,
            market=market,
            as_of=as_of,
            sources=sources,
            fetched_at=utc_now_iso(),
            collection_status=statuses,
            price_data=price_data,
            fundamentals_data=fundamentals_data,
            news_data=news_data,
            provider_errors=errors,
        )
        return raw.model_dump()
