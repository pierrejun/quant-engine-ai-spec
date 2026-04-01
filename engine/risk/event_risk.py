from __future__ import annotations


def apply_event_risk(decision: dict, features: dict) -> dict:
    updated = dict(decision)
    event = features.get("event", {})
    if event.get("has_major_event"):
        updated["risk_flags"] = list(updated["risk_flags"]) + ["major_event"]
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.10), 4)
        if updated["action"] == "buy":
            updated["action"] = "hold"
    earnings_days = event.get("earnings_within_days")
    if earnings_days is not None and 0 <= earnings_days <= 7:
        updated["risk_flags"] = list(updated["risk_flags"]) + ["earnings_near"]
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.07), 4)
        if updated["action"] in {"buy", "sell"}:
            updated["action"] = "observe"
    return updated
