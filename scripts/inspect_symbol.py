from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import load_dotenv
from engine.features.pipeline import FeaturePipeline
from engine.providers.us.finnhub_provider import FinnhubProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect raw and normalized data for a symbol.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--market", default="US")
    parser.add_argument("--as-of", dest="as_of", required=True)
    return parser.parse_args()


def main(symbol: str, market: str, as_of: str) -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    if market.upper() != "US":
        raise ValueError("inspect_symbol.py currently supports US market only.")

    provider = FinnhubProvider()
    price = provider.get_price_data(symbol, market, as_of)
    fundamentals = provider.get_fundamentals_data(symbol, market, as_of)
    news = provider.get_news_data(symbol, market, as_of)
    raw_data = {
        "symbol": symbol,
        "market": market,
        "as_of": as_of,
        "price_data": price,
        "fundamentals_data": fundamentals,
        "news_data": news,
    }
    features = FeaturePipeline().extract(raw_data)

    report = {
        "symbol": symbol,
        "market": market,
        "as_of": as_of,
        "sources": {
            "price": price.get("source"),
            "fundamentals": fundamentals.get("source"),
            "news": news[0].get("source") if news else None,
        },
        "price_last_row": price["history"][-1],
        "price_previous_row": price["history"][-2] if len(price["history"]) >= 2 else None,
        "fundamentals_normalized": {
            key: fundamentals.get(key)
            for key in [
                "pe_ttm",
                "pb_ttm",
                "gross_margin_ttm",
                "revenue_growth_ttm_yoy",
                "net_margin",
                "next_earnings_date",
            ]
        },
        "fundamentals_metric_keys": sorted((fundamentals.get("metric") or {}).keys()),
        "news_count": len(news),
        "news_sample": news[:5],
        "features": features,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    args = parse_args()
    main(args.symbol.upper(), args.market.upper(), args.as_of)
