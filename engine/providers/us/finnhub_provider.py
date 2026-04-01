from __future__ import annotations

import os
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from engine.common import utc_now_iso
from engine.exceptions import ProviderError


class FinnhubProvider:
    base_url = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 10) -> None:
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.timeout_seconds = timeout_seconds

    def _get(self, endpoint: str, params: dict) -> dict | list:
        if not self.api_key:
            raise ProviderError("FINNHUB_API_KEY is not configured")
        request = Request(
            f"{self.base_url}/{endpoint}?{urlencode({**params, 'token': self.api_key})}",
            headers={"User-Agent": "quant-decision-engine/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise ProviderError(f"Finnhub request failed: {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, dict) and payload.get("error"):
            raise ProviderError(f"Finnhub error: {payload['error']}")
        return payload

    def get_price_data(self, symbol: str, market: str, as_of: str) -> dict:
        end_date = datetime.fromisoformat(as_of).date()
        start_date = end_date - timedelta(days=240)
        payload = self._get(
            "stock/candle",
            {
                "symbol": symbol,
                "resolution": "D",
                "from": int(datetime.combine(start_date, datetime.min.time(), UTC).timestamp()),
                "to": int(datetime.combine(end_date + timedelta(days=1), datetime.min.time(), UTC).timestamp()),
            },
        )
        if payload.get("s") != "ok":
            raise ProviderError(f"Finnhub candle request failed: status={payload.get('s')}")

        closes = payload.get("c") or []
        highs = payload.get("h") or []
        lows = payload.get("l") or []
        volumes = payload.get("v") or []
        timestamps = payload.get("t") or []

        rows = []
        for idx, ts in enumerate(timestamps):
            close = closes[idx] if idx < len(closes) else None
            if close is None:
                continue
            rows.append(
                {
                    "date": datetime.fromtimestamp(ts, UTC).date().isoformat(),
                    "close": float(close),
                    "high": float(highs[idx]) if idx < len(highs) and highs[idx] is not None else float(close),
                    "low": float(lows[idx]) if idx < len(lows) and lows[idx] is not None else float(close),
                    "volume": float(volumes[idx]) if idx < len(volumes) and volumes[idx] is not None else 0.0,
                }
            )
        if len(rows) < 20:
            raise ProviderError("Finnhub price history shorter than 20 bars")
        avg_volume_20 = sum(row["volume"] for row in rows[-20:]) / len(rows[-20:])
        return {
            "source": "finnhub",
            "fetched_at": utc_now_iso(),
            "history": rows,
            "latest_close": rows[-1]["close"],
            "average_volume_20d": avg_volume_20,
        }

    def get_fundamentals_data(self, symbol: str, market: str, as_of: str) -> dict:
        metrics = self._get("stock/metric", {"symbol": symbol, "metric": "all"})
        metric = metrics.get("metric", {})
        return {
            "source": "finnhub",
            "fetched_at": utc_now_iso(),
            "metric": metric,
            "pe_ttm": metric.get("peTTM"),
            "pb_ttm": metric.get("pbQuarterly"),
            "gross_margin_ttm": self._normalize_percent(metric.get("grossMarginTTM")),
            "revenue_growth_ttm_yoy": self._normalize_percent(metric.get("revenueGrowthTTMYoy")),
            "net_margin": metric.get("netMargin"),
            "next_earnings_date": metric.get("earningsAnnouncement"),
        }

    def get_news_data(self, symbol: str, market: str, as_of: str) -> list[dict]:
        end_date = datetime.fromisoformat(as_of).date()
        start_date = end_date - timedelta(days=3)
        payload = self._get(
            "company-news",
            {"symbol": symbol, "from": start_date.isoformat(), "to": end_date.isoformat()},
        )
        news_items = []
        for item in payload:
            news_items.append(
                {
                    "headline": item.get("headline"),
                    "summary": item.get("summary"),
                    "datetime": datetime.fromtimestamp(item["datetime"], UTC).isoformat() if item.get("datetime") else None,
                    "source": item.get("source", "finnhub"),
                    "sentiment": item.get("sentiment"),
                    "url": item.get("url"),
                    "category": item.get("category"),
                }
            )
        return news_items

    def healthcheck(self) -> dict:
        return {"provider": "finnhub", "status": "configured" if self.api_key else "missing_api_key"}

    def _normalize_percent(self, value):
        if value is None:
            return None
        value = float(value)
        if abs(value) > 1:
            return value / 100.0
        return value
