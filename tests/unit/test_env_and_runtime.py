import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import load_dotenv
from engine.runtime import build_pipeline_for_market


class EnvAndRuntimeTests(unittest.TestCase):
    def test_load_dotenv_sets_missing_values_only(self) -> None:
        env_path = PROJECT_ROOT / "tests" / "fixtures" / "tmp_test.env"
        env_path.write_text("EXAMPLE_KEY=example-value\n", encoding="utf-8")
        os.environ.pop("EXAMPLE_KEY", None)
        load_dotenv(env_path)
        self.assertEqual(os.getenv("EXAMPLE_KEY"), "example-value")

    def test_build_pipeline_for_cn_demo(self) -> None:
        pipeline = build_pipeline_for_market(PROJECT_ROOT, market="CN", use_demo_data=True)
        self.assertIn("collector", pipeline)
        self.assertIn("decision_engine", pipeline)

    def test_build_pipeline_for_us_demo(self) -> None:
        pipeline = build_pipeline_for_market(PROJECT_ROOT, market="US", use_demo_data=True)
        self.assertIn("collector", pipeline)
        self.assertIn("report_renderer", pipeline)

    def test_build_pipeline_for_us_live_uses_stable_provider_split(self) -> None:
        pipeline = build_pipeline_for_market(PROJECT_ROOT, market="US", use_demo_data=False)
        collector = pipeline["collector"]
        self.assertEqual(collector.price_collector.provider.__class__.__name__, "YahooProvider")
        self.assertEqual(collector.fundamentals_collector.provider.__class__.__name__, "FinnhubProvider")
        self.assertEqual(collector.news_collector.provider.__class__.__name__, "FinnhubProvider")


if __name__ == "__main__":
    unittest.main()
