from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from statistics import fmean
from urllib.parse import urlencode

from urllib.request import Request, urlopen

from engine.common import utc_now_iso
from engine.exceptions import ProviderError


class YahooProvider:
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def get_price_data(self, symbol: str, market: str, as_of: str) -> dict:
        end_dt = datetime.fromisoformat(as_of).replace(tzinfo=UTC) + timedelta(days=1)
        start_dt = end_dt - timedelta(days=180)
        params = {
            "period1": int(start_dt.timestamp()),
            "period2": int(end_dt.timestamp()),
            "interval": "1d",
            "includePrePost": "false",
            "events": "div,splits",
        }
        request = Request(
            f"{self.base_url.format(symbol=symbol)}?{urlencode(params)}",
            headers={"User-Agent": "quant-decision-engine/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise ProviderError(f"Yahoo price request failed: {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
        result = payload.get("chart", {}).get("result") or []
        if not result:
            raise ProviderError("Yahoo price payload missing result")
        item = result[0]
        timestamps = item.get("timestamp") or []
        quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        volumes = quote.get("volume") or []
        rows = []
        for idx, ts in enumerate(timestamps):
            close = closes[idx] if idx < len(closes) else None
            if close is None:
                continue
            rows.append(
                {
                    "date": datetime.fromtimestamp(ts, UTC).date().isoformat(),
                    "close": close,
                    "high": highs[idx] if idx < len(highs) and highs[idx] is not None else close,
                    "low": lows[idx] if idx < len(lows) and lows[idx] is not None else close,
                    "volume": volumes[idx] if idx < len(volumes) and volumes[idx] is not None else 0,
                }
            )
        if len(rows) < 20:
            raise ProviderError("Yahoo price history shorter than 20 bars")
        avg_volume_20 = fmean([row["volume"] for row in rows[-20:]]) if rows[-20:] else 0.0
        return {
            "source": "yahoo",
            "fetched_at": utc_now_iso(),
            "history": rows,
            "latest_close": rows[-1]["close"],
            "average_volume_20d": avg_volume_20,
        }

    def get_fundamentals_data(self, symbol: str, market: str, as_of: str) -> dict:
        raise ProviderError("Yahoo fundamentals provider not enabled for MVP")

    def get_news_data(self, symbol: str, market: str, as_of: str) -> list[dict]:
        raise ProviderError("Yahoo news provider not enabled for MVP")

    def healthcheck(self) -> dict:
        return {"provider": "yahoo", "status": "configured"}
