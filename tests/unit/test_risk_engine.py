import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import load_yaml
from engine.risk.risk_engine import RuleBasedRiskEngine


class RiskEngineTests(unittest.TestCase):
    def test_risk_engine_downgrades_buy_when_fundamentals_missing(self) -> None:
        thresholds = load_yaml(PROJECT_ROOT / "configs" / "thresholds.yaml")
        engine = RuleBasedRiskEngine(thresholds=thresholds)
        decision = {
            "action": "buy",
            "confidence": 0.8,
            "risk_flags": [],
            "bullish_score": 0.7,
            "bearish_score": 0.2,
            "uncertainty_score": 0.1,
            "data_quality_score": 0.7,
        }
        raw_data = {"collection_status": {"price": "ok", "fundamentals": "error", "news": "ok"}}
        features = {"event": {}, "technical": {"atr_pct": 0.01}}
        updated = engine.apply(decision, raw_data, features, [])
        self.assertEqual(updated["action"], "observe")
        self.assertIn("fundamentals_missing", updated["risk_flags"])


if __name__ == "__main__":
    unittest.main()
