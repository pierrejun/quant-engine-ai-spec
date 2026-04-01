from __future__ import annotations

from datetime import date
from pathlib import Path

from engine.querying.cache import load_cached_analysis
from engine.querying.formatter import format_resolution_message, format_result_message, format_unsupported_message
from engine.querying.resolver import ResolvedSymbol, SymbolResolver
from scripts.run_single import main as run_single


class QueryService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.resolver = SymbolResolver(self.project_root)

    def prepare_query(self, query: str, as_of: str | None = None, use_demo_data: bool = False) -> dict:
        analysis_date = as_of or date.today().isoformat()
        resolution = self.resolver.resolve(query)
        if resolution is None:
            return {
                "status": "unresolved",
                "query": query,
                "as_of": analysis_date,
                "message": f"未识别输入: {query}。请补充更明确的股票代码或名称。",
            }

        cached = None
        if resolution.supported:
            cached = load_cached_analysis(
                self.project_root,
                symbol=resolution.symbol,
                market=resolution.market,
                as_of=analysis_date,
                run_tag="demo" if use_demo_data else "live",
            )
        payload = {
            "status": "ready" if resolution.supported else "unsupported_market",
            "query": query,
            "as_of": analysis_date,
            "resolution": resolution.model_dump(),
            "cache_hit": cached is not None,
            "cached_summary": self._build_cached_summary(cached),
        }
        if resolution.supported:
            payload["message"] = format_resolution_message(payload["resolution"], analysis_date, payload["cache_hit"])
        else:
            payload["message"] = format_unsupported_message(payload["resolution"])
        return payload

    def execute_query(
        self,
        query: str,
        as_of: str | None = None,
        use_demo_data: bool = False,
        force_refresh: bool = False,
    ) -> dict:
        prepared = self.prepare_query(query, as_of=as_of, use_demo_data=use_demo_data)
        if prepared["status"] != "ready":
            return prepared

        resolution = ResolvedSymbol(**prepared["resolution"])
        if prepared["cache_hit"] and not force_refresh:
            result = load_cached_analysis(
                self.project_root,
                symbol=resolution.symbol,
                market=resolution.market,
                as_of=prepared["as_of"],
                run_tag="demo" if use_demo_data else "live",
            )
            return {
                **prepared,
                "status": "completed",
                "from_cache": True,
                "result": result,
                "message": format_result_message(result, from_cache=True),
            }

        result = run_single(
            symbol=resolution.symbol,
            market=resolution.market,
            as_of=prepared["as_of"],
            use_demo_data=use_demo_data,
        )
        return {
            **prepared,
            "status": "completed",
            "from_cache": False,
            "result": result,
            "message": format_result_message(result, from_cache=False),
        }

    def _build_cached_summary(self, cached: dict | None) -> dict | None:
        if cached is None:
            return None
        state = cached.get("state") or {}
        artifacts = state.get("artifacts") or {}
        decision = cached.get("decision") or {}
        return {
            "job_id": cached.get("job_id"),
            "status": state.get("status"),
            "action": decision.get("action"),
            "confidence": decision.get("confidence"),
            "report_path": artifacts.get("report_path"),
            "detail_report_path": artifacts.get("detail_report_path"),
            "final_json_path": artifacts.get("final_json_path"),
        }
