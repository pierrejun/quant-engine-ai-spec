import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import save_json
from engine.querying.cache import get_cached_analysis_path, load_cached_analysis
from engine.querying.service import QueryService


class QueryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = QueryService(PROJECT_ROOT)

    def test_prepare_query_resolves_cn_name(self) -> None:
        result = self.service.prepare_query("兴业银行", as_of="2026-03-27")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["resolution"]["symbol"], "601166.SH")
        self.assertEqual(result["resolution"]["market"], "CN")

    def test_prepare_query_marks_unsupported_market(self) -> None:
        result = self.service.prepare_query("小米", as_of="2026-03-27")
        self.assertEqual(result["status"], "unsupported_market")
        self.assertFalse(result["resolution"]["supported"])

    def test_load_cached_analysis_reads_completed_payload(self) -> None:
        path = get_cached_analysis_path(PROJECT_ROOT, "NVDA", "US", "2026-03-28", run_tag="demo")
        save_json(
            {
                "state": {
                    "status": "completed",
                    "symbol": "NVDA",
                    "market": "US",
                    "as_of": "2026-03-28",
                    "artifacts": {},
                },
                "decision": {"action": "hold", "confidence": 0.5, "risk_flags": []},
                "raw_data": {"sources": {"price": "demo_yahoo", "fundamentals": "demo_finnhub", "news": "demo"}},
            },
            path,
        )
        cached = load_cached_analysis(PROJECT_ROOT, "NVDA", "US", "2026-03-28", run_tag="demo")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["state"]["symbol"], "NVDA")


if __name__ == "__main__":
    unittest.main()
