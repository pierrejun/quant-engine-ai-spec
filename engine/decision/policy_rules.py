from __future__ import annotations


def map_score_to_action(final_score: float, data_quality_score: float, thresholds: dict[str, float]) -> tuple[str, str]:
    if data_quality_score < thresholds["data_quality"]["insufficient"]:
        return "insufficient_data", "insufficient_data"
    decision_thresholds = thresholds["decision"]
    if final_score >= decision_thresholds["buy"]:
        return "buy", "buy"
    if final_score >= decision_thresholds["hold_positive"]:
        return "hold", "hold_positive"
    if final_score >= decision_thresholds["observe"]:
        return "observe", "observe"
    if final_score >= decision_thresholds["hold_negative"]:
        return "hold", "hold_negative"
    return "sell", "sell"
