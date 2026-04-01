import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import load_yaml
from engine.decision.decision_engine import RuleBasedDecisionEngine


class DecisionEngineTests(unittest.TestCase):
    def test_decision_engine_outputs_single_action(self) -> None:
        weights = load_yaml(PROJECT_ROOT / "configs" / "weights.yaml")
        thresholds = load_yaml(PROJECT_ROOT / "configs" / "thresholds.yaml")
        engine = RuleBasedDecisionEngine(weights=weights, thresholds=thresholds)
        evidence = [
            {"factor": "A", "category": "technical", "direction": "bullish", "strength": 0.7, "confidence": 0.8},
            {"factor": "B", "category": "fundamentals", "direction": "bearish", "strength": 0.3, "confidence": 0.7},
        ]
        raw_data = {"collection_status": {"price": "ok", "fundamentals": "ok", "news": "ok"}, "price_data": {"history": [1] * 80}, "provider_errors": []}
        decision = engine.decide(evidence, meta={"raw_data": raw_data})
        self.assertIn(decision["action"], {"buy", "hold", "sell", "observe", "insufficient_data"})
        self.assertIsInstance(decision["confidence"], float)


if __name__ == "__main__":
    unittest.main()
