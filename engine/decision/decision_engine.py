from __future__ import annotations

from engine.decision.base import BaseDecisionEngine
from engine.decision.consistency_checker import build_conflict_flags
from engine.decision.policy_rules import map_score_to_action
from engine.decision.scoring import aggregate_scores
from engine.exceptions import DecisionError
from engine.models.decision import Decision


class RuleBasedDecisionEngine(BaseDecisionEngine):
    def __init__(self, weights: dict, thresholds: dict) -> None:
        self.weights = weights
        self.thresholds = thresholds

    def decide(self, evidences: list[dict], meta: dict | None = None) -> dict:
        try:
            scores = aggregate_scores(evidences, self.weights["category_weights"])
            bullish = round(scores["bullish"], 4)
            bearish = round(scores["bearish"], 4)
            uncertainty = round(scores["neutral"], 4)
            raw_data = (meta or {}).get("raw_data", {})
            final_score = bullish - (bearish * 0.5)
            quality_score = self._data_quality_score(raw_data)
            action, internal_action = map_score_to_action(final_score, quality_score, self.thresholds)
            flags = list(raw_data.get("provider_errors", []))
            flags.extend(build_conflict_flags(bullish, bearish, uncertainty, self.thresholds))
            bullish_top = [item["factor"] for item in evidences if item["direction"] == "bullish"][:3]
            bearish_top = [item["factor"] for item in evidences if item["direction"] == "bearish"][:3]
            confidence = round(max(0.1, min(0.95, 1 - uncertainty * 0.6 - max(0.0, 0.6 - quality_score))), 4)
            decision = Decision(
                action=action,
                confidence=confidence,
                bullish_score=bullish,
                bearish_score=bearish,
                uncertainty_score=uncertainty,
                data_quality_score=quality_score,
                risk_flags=flags,
                top_bullish_evidence=bullish_top,
                top_bearish_evidence=bearish_top,
                internal_action=internal_action,
            )
            return decision.model_dump()
        except Exception as exc:
            raise DecisionError(str(exc)) from exc

    def _data_quality_score(self, raw_data: dict) -> float:
        status = raw_data.get("collection_status", {})
        penalties = 0.0
        if status.get("news") != "ok":
            penalties += self.thresholds["data_quality"]["degraded_news_penalty"]
        if status.get("fundamentals") != "ok":
            penalties += self.thresholds["data_quality"]["degraded_fundamentals_penalty"]
        history = raw_data.get("price_data", {}).get("history", [])
        if len(history) < 60:
            penalties += self.thresholds["data_quality"]["short_price_history_penalty"]
        return round(max(0.0, 1 - penalties), 4)
