from __future__ import annotations


def extract_valuation_features(raw_data: dict) -> dict:
    fundamentals = raw_data.get("fundamentals_data", {})
    pe = fundamentals.get("pe_ttm")
    pb = fundamentals.get("pb_ttm")
    pe_percentile = None if pe is None else min(max(pe / 40, 0.0), 1.0)
    pb_percentile = None if pb is None else min(max(pb / 20, 0.0), 1.0)
    return {
        "pe_ttm": pe,
        "pe_percentile_3y": round(pe_percentile, 4) if pe_percentile is not None else None,
        "pb_ttm": pb,
        "pb_percentile_3y": round(pb_percentile, 4) if pb_percentile is not None else None,
    }
