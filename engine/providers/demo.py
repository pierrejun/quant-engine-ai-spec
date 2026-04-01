from __future__ import annotations

from copy import deepcopy

from engine.common import utc_now_iso


DEMO_PRICE_HISTORY = [
    {"date": f"2026-01-{day:02d}", "close": 120 + day * 0.8, "high": 121 + day * 0.8, "low": 119 + day * 0.8, "volume": 1000000 + day * 15000}
    for day in range(1, 31)
] + [
    {"date": f"2026-02-{day:02d}", "close": 144 + day * 0.9, "high": 145 + day * 0.9, "low": 143 + day * 0.9, "volume": 1500000 + day * 22000}
    for day in range(1, 29)
] + [
    {"date": f"2026-03-{day:02d}", "close": 170 + day * 1.1, "high": 171 + day * 1.1, "low": 169 + day * 1.1, "volume": 1900000 + day * 35000}
    for day in range(1, 28)
]

DEMO_FUNDAMENTALS = {
    "metric": {
        "peTTM": 28.3,
        "pbQuarterly": 19.1,
        "grossMarginTTM": 0.742,
        "revenueGrowthTTMYoy": 0.21,
        "netMargin": 0.31,
        "earningsAnnouncement": "2026-05-15",
    }
}

DEMO_NEWS = [
    {"headline": "Demand remains resilient", "summary": "Channel checks point to stable demand.", "datetime": "2026-03-25T12:00:00+00:00", "source": "demo", "sentiment": 0.25, "url": "https://example.com/news/1", "category": "company"},
    {"headline": "Valuation debate intensifies", "summary": "Analysts discuss rich multiples.", "datetime": "2026-03-26T10:30:00+00:00", "source": "demo", "sentiment": -0.05, "url": "https://example.com/news/2", "category": "company"},
    {"headline": "AI infrastructure spending stays strong", "summary": "Enterprise budgets remain supportive.", "datetime": "2026-03-27T08:15:00+00:00", "source": "demo", "sentiment": 0.18, "url": "https://example.com/news/3", "category": "industry"},
]


class DemoProvider:
    def get_price_data(self, symbol: str, market: str, as_of: str) -> dict:
        return {
            "source": "demo_yahoo",
            "fetched_at": utc_now_iso(),
            "history": deepcopy(DEMO_PRICE_HISTORY),
            "latest_close": DEMO_PRICE_HISTORY[-1]["close"],
            "average_volume_20d": sum(item["volume"] for item in DEMO_PRICE_HISTORY[-20:]) / 20,
        }

    def get_fundamentals_data(self, symbol: str, market: str, as_of: str) -> dict:
        payload = deepcopy(DEMO_FUNDAMENTALS)
        payload.update(
            {
                "source": "demo_finnhub",
                "fetched_at": utc_now_iso(),
                "pe_ttm": payload["metric"]["peTTM"],
                "pb_ttm": payload["metric"]["pbQuarterly"],
                "gross_margin_ttm": payload["metric"]["grossMarginTTM"],
                "revenue_growth_ttm_yoy": payload["metric"]["revenueGrowthTTMYoy"],
                "net_margin": payload["metric"]["netMargin"],
                "next_earnings_date": payload["metric"]["earningsAnnouncement"],
            }
        )
        return payload

    def get_news_data(self, symbol: str, market: str, as_of: str) -> list[dict]:
        return deepcopy(DEMO_NEWS)

    def healthcheck(self) -> dict:
        return {"provider": "demo", "status": "ready"}
