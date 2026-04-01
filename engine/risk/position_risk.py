from __future__ import annotations


def apply_conflict_risk(decision: dict) -> dict:
    updated = dict(decision)
    flags = set(updated.get("risk_flags", []))
    if "conflicting_evidence" in flags or "high_uncertainty" in flags:
        updated["confidence"] = round(max(0.05, updated["confidence"] - 0.10), 4)
        if updated["action"] in {"buy", "sell"}:
            updated["action"] = "hold"
    return updated
