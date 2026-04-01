from __future__ import annotations


def apply_regime_risk(decision: dict, features: dict, thresholds: dict) -> dict:
    updated = dict(decision)
    technical = features.get("technical", {})
    if technical.get("atr_pct", 0.0) >= thresholds["risk"]["high_volatility_atr_pct"]:
        updated["risk_flags"] = list(updated["risk_flags"]) + ["high_volatility"]
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.08), 4)
        if updated["action"] == "buy":
            updated["action"] = "hold"
    return updated
