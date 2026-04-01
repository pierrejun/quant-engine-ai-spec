import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_single import main


class RunSingleIntegrationTests(unittest.TestCase):
    def test_run_single_creates_all_artifacts(self) -> None:
        result = main("NVDA", "US", "2026-03-27", use_demo_data=True)
        state = result["state"]
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["job_id"], "20260327_US_NVDA_001_DEMO")
        self.assertTrue(Path(state["artifacts"]["raw_snapshot_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["features_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["evidence_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["decision_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["report_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["detail_report_path"]).exists())
        self.assertTrue(Path(state["artifacts"]["final_json_path"]).exists())
        self.assertTrue((PROJECT_ROOT / "data" / "logs" / "20260327_US_NVDA_001_DEMO.log").exists())
        report_text = Path(state["artifacts"]["report_path"]).read_text(encoding="utf-8")
        detail_report_text = Path(state["artifacts"]["detail_report_path"]).read_text(encoding="utf-8")
        self.assertIn("运行模式", report_text)
        self.assertIn("DEMO", report_text)
        self.assertIn("## 3. 技术分析", report_text)
        self.assertIn("## 4. 基本面分析", report_text)
        self.assertIn("## 5. 估值分析", report_text)
        self.assertIn("## 6. 新闻与市场情绪", report_text)
        self.assertIn("运行模式", detail_report_text)
        self.assertIn("DEMO", detail_report_text)
        self.assertIn("## 一、投资要点", detail_report_text)
        self.assertIn("## 十、决策依据与后续观察", detail_report_text)


if __name__ == "__main__":
    unittest.main()
