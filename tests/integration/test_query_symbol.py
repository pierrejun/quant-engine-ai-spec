import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.query_symbol import main


class QuerySymbolIntegrationTests(unittest.TestCase):
    def test_query_symbol_prepare_then_confirm_uses_cache(self) -> None:
        prepared = main("NVDA", "2026-03-27", use_demo_data=True, confirm=False)
        self.assertEqual(prepared["status"], "ready")
        executed = main("NVDA", "2026-03-27", use_demo_data=True, confirm=True)
        self.assertEqual(executed["status"], "completed")
        second = main("NVDA", "2026-03-27", use_demo_data=True, confirm=True)
        self.assertEqual(second["status"], "completed")
        self.assertTrue(second["from_cache"])


if __name__ == "__main__":
    unittest.main()
