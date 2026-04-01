from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

from engine.common import env_flag, utc_now_iso
from engine.exceptions import ProviderError


class TushareProvider:
    base_url = "https://api.tushare.pro"

    def __init__(self, token: str | None = None, timeout_seconds: int = 10) -> None:
        self.token = token or os.getenv("TUSHARE_TOKEN")
        self.timeout_seconds = timeout_seconds
        self.enabled = env_flag("TUSHARE_ENABLED", False)

    def _post(self, api_name: str, params: dict, fields: str) -> list[dict]:
        if not self.enabled:
            raise ProviderError("TUSHARE_ENABLED is false")
        if not self.token:
            raise ProviderError("TUSHARE_TOKEN is not configured")
        payload = json.dumps(
            {
                "api_name": api_name,
                "token": self.token,
                "params": params,
                "fields": fields,
            }
        ).encode("utf-8")
        request = Request(
            self.base_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "quant-decision-engine/0.1"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise ProviderError(f"Tushare request failed: {response.status}")
            body = json.loads(response.read().decode("utf-8"))
        if body.get("code") != 0:
            raise ProviderError(f"Tushare error: {body.get('msg', 'unknown error')}")
        data = body.get("data") or {}
        fields_list = data.get("fields") or []
        items = data.get("items") or []
        return [dict(zip(fields_list, row)) for row in items]

    def get_price_data(self, symbol: str, market: str, as_of: str) -> dict:
        end_date = datetime.fromisoformat(as_of).date()
        start_date = end_date - timedelta(days=180)
        rows = self._post(
            api_name="daily",
            params={"ts_code": symbol, "start_date": start_date.strftime("%Y%m%d"), "end_date": end_date.strftime("%Y%m%d")},
            fields="ts_code,trade_date,open,high,low,close,vol",
        )
        history = [
            {
                "date": datetime.strptime(item["trade_date"], "%Y%m%d").date().isoformat(),
                "close": float(item["close"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "volume": float(item["vol"]),
            }
            for item in reversed(rows)
            if item.get("close") is not None
        ]
        if len(history) < 20:
            raise ProviderError("Tushare price history shorter than 20 bars")
        avg_volume_20 = sum(item["volume"] for item in history[-20:]) / 20
        return {
            "source": "tushare",
            "fetched_at": utc_now_iso(),
            "history": history,
            "latest_close": history[-1]["close"],
            "average_volume_20d": avg_volume_20,
        }

    def get_fundamentals_data(self, symbol: str, market: str, as_of: str) -> dict:
        basic_rows = self._post(
            api_name="daily_basic",
            params={"ts_code": symbol, "trade_date": datetime.fromisoformat(as_of).strftime("%Y%m%d")},
            fields="ts_code,trade_date,pe_ttm,pb",
        )
        fina_rows = self._post(
            api_name="fina_indicator",
            params={"ts_code": symbol, "limit": 1},
            fields="ts_code,end_date,q_sales_yoy,q_dtprofit_yoy,grossprofit_margin",
        )
        basic = basic_rows[0] if basic_rows else {}
        fina = fina_rows[0] if fina_rows else {}
        return {
            "source": "tushare",
            "fetched_at": utc_now_iso(),
            "pe_ttm": basic.get("pe_ttm"),
            "pb_ttm": basic.get("pb"),
            "gross_margin_ttm": (float(fina["grossprofit_margin"]) / 100.0) if fina.get("grossprofit_margin") is not None else None,
            "revenue_growth_ttm_yoy": (float(fina["q_sales_yoy"]) / 100.0) if fina.get("q_sales_yoy") is not None else None,
            "net_margin": (float(fina["q_dtprofit_yoy"]) / 100.0) if fina.get("q_dtprofit_yoy") is not None else None,
            "next_earnings_date": None,
        }

    def get_news_data(self, symbol: str, market: str, as_of: str) -> list[dict]:
        raise ProviderError("Tushare news provider is not configured for MVP")

    def healthcheck(self) -> dict:
        if not self.enabled:
            return {"provider": "tushare", "status": "disabled"}
        return {"provider": "tushare", "status": "configured" if self.token else "missing_token"}
