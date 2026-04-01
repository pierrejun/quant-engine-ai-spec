from __future__ import annotations


def apply_data_quality_risk(decision: dict, raw_data: dict) -> dict:
    updated = dict(decision)
    status = raw_data.get("collection_status", {})
    if status.get("fundamentals") != "ok":
        updated["risk_flags"] = list(updated["risk_flags"]) + ["fundamentals_missing"]
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.20), 4)
        if updated["action"] == "buy":
            updated["action"] = "observe"
    if status.get("news") != "ok":
        updated["risk_flags"] = list(updated["risk_flags"]) + ["news_missing"]
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.08), 4)
        if updated["action"] == "buy":
            updated["action"] = "hold"
    return updated
