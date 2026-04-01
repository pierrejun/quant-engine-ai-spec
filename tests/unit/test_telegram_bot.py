import sys
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.push.telegram_bot_clean import TelegramMessageHandler, TelegramSessionStore


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
            "resolution": {
                "symbol": "NVDA",
                "market": "US",
                "display_name": "NVIDIA",
                "matched_by": "alias",
                "confidence": 0.98,
                "supported": True,
            },
            "cache_hit": False,
            "message": "识别结果: NVIDIA / NVDA / US",
        }

    def execute_query(
        self,
        query: str,
        as_of: str | None = None,
        use_demo_data: bool = False,
        force_refresh: bool = False,
    ) -> dict:
        self.execute_calls.append((query, as_of, use_demo_data, force_refresh))
        return {
            "status": "completed",
            "message": "新触发分析: NVDA / US / 2026-04-01",
        }


class TelegramBotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_dir = PROJECT_ROOT / "data" / "runtime" / f"telegram_test_{uuid4().hex}"
        self.session_path = self.runtime_dir / "test_telegram_sessions.json"
        self.query_service = FakeQueryService()
        self.handler = TelegramMessageHandler(
            query_service=self.query_service,
            session_store=TelegramSessionStore(self.session_path),
            use_demo_data=False,
        )

    def tearDown(self) -> None:
        if self.runtime_dir.exists():
            shutil.rmtree(self.runtime_dir, ignore_errors=True)

    def test_prepare_then_confirm_flow(self) -> None:
        prepare_messages = self.handler.handle_update(
            {
                "message": {
                    "message_id": 1,
                    "chat": {"id": 101},
                    "text": "NVDA",
                }
            }
        )
        self.assertEqual(len(prepare_messages), 1)
        self.assertIn("识别结果", prepare_messages[0].text)
        confirm_messages = self.handler.handle_update(
            {
                "message": {
                    "message_id": 2,
                    "chat": {"id": 101},
                    "text": "确认",
                }
            }
        )
        self.assertEqual(len(confirm_messages), 2)
        self.assertIn("新触发分析", confirm_messages[0].text)
        self.assertIn("/report", confirm_messages[1].text)
        self.assertEqual(self.query_service.execute_calls[0][0], "NVDA")

    def test_confirm_without_pending_task(self) -> None:
        messages = self.handler.handle_update(
            {
                "message": {
                    "message_id": 3,
                    "chat": {"id": 102},
                    "text": "确认",
                }
            }
        )
        self.assertIn("当前没有待确认任务", messages[0].text)

    def test_run_command_bypasses_prepare(self) -> None:
        messages = self.handler.handle_update(
            {
                "message": {
                    "message_id": 4,
                    "chat": {"id": 103},
                    "text": "/run 兴业银行",
                }
            }
        )
        self.assertEqual(len(messages), 2)
        self.assertEqual(self.query_service.execute_calls[0][0], "兴业银行")


if __name__ == "__main__":
    unittest.main()
