from __future__ import annotations


def build_conflict_flags(bullish_score: float, bearish_score: float, uncertainty_score: float, thresholds: dict[str, float]) -> list[str]:
    flags: list[str] = []
    if abs(bullish_score - bearish_score) <= thresholds["risk"]["conflicting_gap_max"]:
        flags.append("conflicting_evidence")
    if uncertainty_score >= thresholds["risk"]["uncertainty_high"]:
        flags.append("high_uncertainty")
    return flags
