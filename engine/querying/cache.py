from __future__ import annotations

from pathlib import Path

from engine.common import build_job_id, read_json


def get_cached_analysis_path(project_root: Path, symbol: str, market: str, as_of: str, run_tag: str = "live") -> Path:
    job_id = build_job_id(symbol, market, as_of, run_tag=run_tag)
    return Path(project_root) / "data" / "outputs" / f"{job_id}.json"


def load_cached_analysis(project_root: Path, symbol: str, market: str, as_of: str, run_tag: str = "live") -> dict | None:
    target = get_cached_analysis_path(project_root, symbol, market, as_of, run_tag=run_tag)
    if not target.exists():
        return None
    payload = read_json(target)
    state = payload.get("state") or {}
    if state.get("status") != "completed":
        return None
    return payload
