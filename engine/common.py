from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from engine.models.state import AnalysisArtifacts, AnalysisState


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data: Any, path: str | Path) -> None:
    target = Path(path)
    ensure_dir(target.parent)
    if is_dataclass(data):
        data = asdict(data)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def save_text(text: str, path: str | Path) -> None:
    target = Path(path)
    ensure_dir(target.parent)
    with target.open("w", encoding="utf-8") as handle:
        handle.write(text)


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_job_id(symbol: str, market: str, as_of: str | None, run_tag: str | None = None) -> str:
    stamp = (as_of or date.today().isoformat()).replace("-", "")
    base = f"{stamp}_{market.upper()}_{symbol.upper()}_001"
    if run_tag:
        return f"{base}_{run_tag.upper()}"
    return base


def init_state(job_id: str, symbol: str, market: str, as_of: str) -> AnalysisState:
    now = utc_now_iso()
    return AnalysisState(
        job_id=job_id,
        symbol=symbol,
        market=market,
        as_of=as_of,
        status="running",
        stage="collecting",
        started_at=now,
        updated_at=now,
        data_quality={"price": "pending", "fundamentals": "pending", "news": "pending"},
        artifacts=AnalysisArtifacts(),
    )


def touch_state(state: AnalysisState, stage: str | None = None, status: str | None = None) -> AnalysisState:
    if stage is not None:
        state.stage = stage
    if status is not None:
        state.status = status
    state.updated_at = utc_now_iso()
    return state


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_dotenv(path: str | Path) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    original_keys = set(os.environ.keys())
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in original_keys:
            continue
        os.environ[key] = value
