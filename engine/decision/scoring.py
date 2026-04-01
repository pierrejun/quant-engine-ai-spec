from __future__ import annotations

from collections import defaultdict


def aggregate_scores(evidences: list[dict], category_weights: dict[str, float]) -> dict[str, float]:
    directional = defaultdict(float)
    for item in evidences:
        category = item["category"]
        weight = category_weights.get(category, 0.0)
        signed_strength = item["strength"] * item["confidence"] * weight
        if item["direction"] == "bullish":
            directional["bullish"] += signed_strength
        elif item["direction"] == "bearish":
            directional["bearish"] += signed_strength
        else:
            directional["neutral"] += signed_strength
    total = directional["bullish"] + directional["bearish"] + directional["neutral"]
    if total <= 0:
        return {"bullish": 0.0, "bearish": 0.0, "neutral": 1.0}
    return {
        "bullish": directional["bullish"] / total,
        "bearish": directional["bearish"] / total,
        "neutral": directional["neutral"] / total,
    }
