from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from engine.common import ensure_dir, env_flag, load_dotenv, read_json, save_json
from engine.querying.service_clean import QueryService


@dataclass
class OutboundMessage:
    chat_id: int
    text: str
    reply_to_message_id: int | None = None


class TelegramBotClient:
    def __init__(self, token: str, timeout_seconds: int = 30) -> None:
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout_seconds = timeout_seconds

    def get_updates(self, offset: int | None = None, timeout: int = 20) -> list[dict]:
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        return self._post_json("getUpdates", params).get("result", [])

    def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None) -> dict:
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._post_json("sendMessage", payload)

    def _post_json(self, method: str, payload: dict) -> dict:
        request = Request(
            f"{self.base_url}/{method}",
            data=urlencode(payload).encode("utf-8"),
            headers={"User-Agent": "quant-decision-engine/0.1"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok"):
            raise RuntimeError(f"Telegram API error: {body}")
        return body


class TelegramSessionStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def get(self, chat_id: int) -> dict | None:
        return self._load().get(str(chat_id))

    def set(self, chat_id: int, payload: dict) -> None:
        data = self._load()
        data[str(chat_id)] = payload
        self._save(data)

    def delete(self, chat_id: int) -> None:
        data = self._load()
        if str(chat_id) in data:
            del data[str(chat_id)]
            self._save(data)

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        return read_json(self.path)

    def _save(self, data: dict) -> None:
        ensure_dir(self.path.parent)
        save_json(data, self.path)


class TelegramMessageHandler:
    def __init__(self, query_service: QueryService, session_store: TelegramSessionStore, use_demo_data: bool = False) -> None:
        self.query_service = query_service
        self.session_store = session_store
        self.use_demo_data = use_demo_data

    def handle_update(self, update: dict) -> list[OutboundMessage]:
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        message_id = message.get("message_id")
        if not text or chat_id is None:
            return []

        normalized = text.casefold()
        if normalized in {"/start", "/help"}:
            return [OutboundMessage(chat_id, self._build_help_text(), message_id)]
        if normalized in {"/cancel", "取消"}:
            self.session_store.delete(chat_id)
            return [OutboundMessage(chat_id, "已取消当前待确认任务。", message_id)]
        if normalized in {"/confirm", "确认"}:
            return self._confirm(chat_id, message_id)
        if normalized.startswith("/refresh "):
            return self._run_query(chat_id, message_id, text.split(" ", 1)[1].strip(), force_refresh=True)
        if normalized.startswith("/run "):
            return self._run_query(chat_id, message_id, text.split(" ", 1)[1].strip(), force_refresh=False)
        if normalized.startswith("/report "):
            return self._send_report(chat_id, message_id, text.split(" ", 1)[1].strip(), detail=False)
        if normalized.startswith("/detail "):
            return self._send_report(chat_id, message_id, text.split(" ", 1)[1].strip(), detail=True)
        return self._prepare(chat_id, message_id, text)

    def _prepare(self, chat_id: int, message_id: int | None, query: str) -> list[OutboundMessage]:
        prepared = self.query_service.prepare_query(query=query, as_of=date.today().isoformat(), use_demo_data=self.use_demo_data)
        if prepared["status"] in {"unresolved", "unsupported_market"}:
            return [OutboundMessage(chat_id, prepared["message"], message_id)]
        self.session_store.set(chat_id, {"query": query, "as_of": prepared["as_of"], "use_demo_data": self.use_demo_data})
        suffix = "\n回复“确认”开始分析，回复“取消”放弃。本次也支持 `/run 代码` 直接分析。"
        return [OutboundMessage(chat_id, f"{prepared['message']}{suffix}", message_id)]

    def _confirm(self, chat_id: int, message_id: int | None) -> list[OutboundMessage]:
        session = self.session_store.get(chat_id)
        if not session:
            return [OutboundMessage(chat_id, "当前没有待确认任务。先发送股票名称或代码。", message_id)]
        return self._run_query(chat_id, message_id, session["query"], False, session["as_of"], bool(session.get("use_demo_data", self.use_demo_data)))

    def _run_query(
        self,
        chat_id: int,
        message_id: int | None,
        query: str,
        force_refresh: bool,
        as_of: str | None = None,
        use_demo_data: bool | None = None,
    ) -> list[OutboundMessage]:
        result = self.query_service.execute_query(
            query=query,
            as_of=as_of or date.today().isoformat(),
            use_demo_data=self.use_demo_data if use_demo_data is None else use_demo_data,
            force_refresh=force_refresh,
        )
        if result["status"] != "completed":
            return [OutboundMessage(chat_id, result["message"], message_id)]
        self.session_store.delete(chat_id)
        resolution = result.get("resolution") or {}
        symbol_or_name = resolution.get("display_name") or query
        return [
            OutboundMessage(chat_id, result["message"], message_id),
            OutboundMessage(chat_id, f"如需查看当天报告正文，可继续发送 `/report {symbol_or_name}` 或 `/detail {symbol_or_name}`。", message_id),
        ]

    def _send_report(self, chat_id: int, message_id: int | None, query: str, detail: bool) -> list[OutboundMessage]:
        report = self.query_service.get_cached_report_text(query=query, as_of=date.today().isoformat(), use_demo_data=self.use_demo_data, detail=detail)
        if report.get("status") != "completed":
            return [OutboundMessage(chat_id, report["message"], message_id)]
        title = "详细报告" if detail else "标准报告"
        chunks = self._split_text(report["report_text"], 3200)
        messages = [OutboundMessage(chat_id, f"{title}: {report['report_path']}", message_id)]
        messages.extend(OutboundMessage(chat_id, chunk, message_id) for chunk in chunks)
        return messages

    def _build_help_text(self) -> str:
        mode_text = "DEMO" if self.use_demo_data else "LIVE"
        return "\n".join(
            [
                "量化分析 Telegram Bot 已启动。",
                f"当前模式: {mode_text}",
                "直接发送股票代码或名称，例如: NVDA、英伟达、兴业银行、601166.SH",
                "流程: 先识别标的，再回复“确认”触发分析。",
                "快捷指令: /run NVDA 直接分析，/refresh NVDA 强制重跑，/report NVDA 查看标准报告，/detail NVDA 查看详细报告，/cancel 取消当前待确认任务。",
            ]
        )

    def _split_text(self, text: str, limit: int) -> list[str]:
        chunks: list[str] = []
        remaining = text.strip()
        while remaining:
            if len(remaining) <= limit:
                chunks.append(remaining)
                break
            boundary = remaining.rfind("\n", 0, limit)
            if boundary <= 0:
                boundary = limit
            chunks.append(remaining[:boundary].strip())
            remaining = remaining[boundary:].strip()
        return chunks


class TelegramBotRunner:
    def __init__(self, project_root: Path, client: TelegramBotClient, handler: TelegramMessageHandler, state_path: Path, poll_timeout: int = 20, retry_interval: int = 5) -> None:
        self.project_root = Path(project_root)
        self.client = client
        self.handler = handler
        self.state_path = Path(state_path)
        self.poll_timeout = poll_timeout
        self.retry_interval = retry_interval

    def run_forever(self) -> None:
        offset = self._load_offset()
        while True:
            try:
                updates = self.client.get_updates(offset=offset, timeout=self.poll_timeout)
                for update in updates:
                    update_id = int(update["update_id"])
                    for outbound in self.handler.handle_update(update):
                        self.client.send_message(outbound.chat_id, outbound.text, outbound.reply_to_message_id)
                    offset = update_id + 1
                    self._save_offset(offset)
            except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
                print(f"[telegram-bot] polling error: {exc}")
                time.sleep(self.retry_interval)

    def _load_offset(self) -> int | None:
        if not self.state_path.exists():
            return None
        return read_json(self.state_path).get("offset")

    def _save_offset(self, offset: int) -> None:
        save_json({"offset": offset}, self.state_path)


def build_telegram_runtime(project_root: Path) -> TelegramBotRunner:
    project_root = Path(project_root)
    load_dotenv(project_root / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    use_demo_data = env_flag("QUANT_ENGINE_USE_DEMO_DATA", False)
    data_dir = project_root / "data" / "runtime"
    session_store = TelegramSessionStore(data_dir / "telegram_sessions.json")
    handler = TelegramMessageHandler(QueryService(project_root), session_store, use_demo_data=use_demo_data)
    client = TelegramBotClient(token)
    return TelegramBotRunner(project_root, client, handler, data_dir / "telegram_bot_state.json")
