from __future__ import annotations


def extract_quality_features(raw_data: dict) -> dict:
    fundamentals = raw_data.get("fundamentals_data", {})
    revenue_yoy = fundamentals.get("revenue_growth_ttm_yoy")
    gross_margin = fundamentals.get("gross_margin_ttm")
    return {
        "revenue_yoy": revenue_yoy,
        "net_income_yoy": None,
        "gross_margin_trend": None,
        "gross_margin_ttm": gross_margin,
    }
