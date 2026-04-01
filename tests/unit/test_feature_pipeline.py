import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.features.pipeline import FeaturePipeline
from engine.providers.demo import DemoProvider


class FeaturePipelineTests(unittest.TestCase):
    def test_feature_pipeline_extracts_expected_sections(self) -> None:
        provider = DemoProvider()
        raw_data = {
            "symbol": "NVDA",
            "market": "US",
            "as_of": "2026-03-27",
            "price_data": provider.get_price_data("NVDA", "US", "2026-03-27"),
            "fundamentals_data": provider.get_fundamentals_data("NVDA", "US", "2026-03-27"),
            "news_data": provider.get_news_data("NVDA", "US", "2026-03-27"),
        }
        features = FeaturePipeline().extract(raw_data)
        self.assertIn("technical", features)
        self.assertIn("valuation", features)
        self.assertIn("quality", features)
        self.assertIn("sentiment", features)
        self.assertIn("event", features)


if __name__ == "__main__":
    unittest.main()
