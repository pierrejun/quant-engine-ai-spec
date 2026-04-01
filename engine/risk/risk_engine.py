from __future__ import annotations

from engine.risk.base import BaseRiskEngine
from engine.risk.data_quality_risk import apply_data_quality_risk
from engine.risk.event_risk import apply_event_risk
from engine.risk.position_risk import apply_conflict_risk
from engine.risk.regime_risk import apply_regime_risk


class RuleBasedRiskEngine(BaseRiskEngine):
    def __init__(self, thresholds: dict) -> None:
        self.thresholds = thresholds

    def apply(self, decision: dict, raw_data: dict, features: dict, evidences: list[dict]) -> dict:
        updated = apply_data_quality_risk(decision, raw_data)
        updated = apply_event_risk(updated, features)
        updated = apply_regime_risk(updated, features, self.thresholds)
        updated = apply_conflict_risk(updated)
        return updated
