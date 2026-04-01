import sys
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.push.telegram_bot_v3 import TelegramMessageHandler, TelegramSessionStore


class FakeQueryService:
    def __init__(self) -> None:
        self.prepare_calls = []
        self.execute_calls = []

    def prepare_query(self, query: str, as_of: str | None = None, use_demo_data: bool = False) -> dict:
        self.prepare_calls.append((query, as_of, use_demo_data))
        return {
            "status": "ready",
            "query": query,
            "as_of": as_of,
            "resolution": {"symbol": "NVDA", "market": "US", "display_name": "NVIDIA", "matched_by": "alias", "confidence": 0.98, "supported": True},
            "cache_hit": False,
            "message": "识别结果: NVIDIA / NVDA / US",
        }

    def execute_query(self, query: str, as_of: str | None = None, use_demo_data: bool = False, force_refresh: bool = False) -> dict:
        self.execute_calls.append((query, as_of, use_demo_data, force_refresh))
        return {
            "status": "completed",
            "message": "偏空结论: NVDA / US / 2026-04-01 (新触发)\n结论: 卖出，置信度 0.95\n一句话建议: 这是最新生成的分析结果。当前偏空信号更强，短线更适合控制风险、谨慎追高。 数据日期为 2026-04-01。\n主要支撑: 营收增速保持为正。\n主要压力: 短期趋势弱于中期趋势；MACD 信号偏空。",
            "followup_message": "查看报告: /report NVDA 或 /detail NVDA",
        }


class TelegramBotV3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_dir = PROJECT_ROOT / "data" / "runtime" / f"telegram_test_{uuid4().hex}"
        self.session_path = self.runtime_dir / "test_telegram_sessions.json"
        self.query_service = FakeQueryService()
        self.handler = TelegramMessageHandler(self.query_service, TelegramSessionStore(self.session_path), use_demo_data=False)

    def tearDown(self) -> None:
        if self.runtime_dir.exists():
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

    def test_prepare_then_confirm_flow(self) -> None:
        prepare_messages = self.handler.handle_update({"message": {"message_id": 1, "chat": {"id": 101}, "text": "NVDA"}})
        self.assertEqual(len(prepare_messages), 1)
        self.assertIn("识别结果", prepare_messages[0].text)
        confirm_messages = self.handler.handle_update({"message": {"message_id": 2, "chat": {"id": 101}, "text": "确认"}})
        self.assertEqual(len(confirm_messages), 2)
        self.assertIn("一句话建议", confirm_messages[0].text)
        self.assertIn("主要压力", confirm_messages[0].text)
        self.assertIn("/report", confirm_messages[1].text)

