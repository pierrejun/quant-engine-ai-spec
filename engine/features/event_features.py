from __future__ import annotations

from datetime import date


def extract_event_features(raw_data: dict) -> dict:
    fundamentals = raw_data.get("fundamentals_data", {})
    earnings_raw = fundamentals.get("next_earnings_date")
    days_until_earnings = None
    if earnings_raw:
        try:
            days_until_earnings = (date.fromisoformat(earnings_raw) - date.fromisoformat(raw_data["as_of"])).days
        except ValueError:
            days_until_earnings = None
    news_items = raw_data.get("news_data", [])
    has_major_event = any(abs(float(item.get("sentiment", 0.0) or 0.0)) >= 0.4 for item in news_items)
    return {
        "has_major_event": has_major_event,
        "earnings_within_days": days_until_earnings,
    }
