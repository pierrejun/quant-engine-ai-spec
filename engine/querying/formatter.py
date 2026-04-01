from __future__ import annotations

ACTION_LABELS = {
    "buy": "买入",
    "hold": "观望",
    "sell": "卖出",
}


def format_resolution_message(resolution: dict, as_of: str, cache_hit: bool) -> str:
    support_text = "支持" if resolution.get("supported") else "暂不支持"
    cache_text = "已存在当日结果" if cache_hit else "当日还没有缓存结果"
    return (
        f"识别结果: {resolution['display_name']} / {resolution['symbol']} / {resolution['market']}\n"
        f"识别方式: {resolution['matched_by']}，置信度: {resolution['confidence']:.2f}\n"
        f"分析日期: {as_of}，系统状态: {support_text}，{cache_text}"
    )


def format_result_message(result: dict, from_cache: bool) -> str:
    decision = result.get("decision") or {}
    state = result.get("state") or {}
    artifacts = state.get("artifacts") or {}
    source_label = "缓存命中" if from_cache else "新触发分析"
    action = ACTION_LABELS.get(decision.get("action"), decision.get("action", "未知"))
    confidence = float(decision.get("confidence") or 0.0)
    risk_flags = decision.get("risk_flags") or []
    raw_data = result.get("raw_data") or {}
    sources = raw_data.get("sources") or {}
    price_source = sources.get("price", "unknown")
    fundamentals_source = sources.get("fundamentals", "unknown")
    news_source = sources.get("news", "unknown")
    return "\n".join(
        [
            f"{source_label}: {state.get('symbol')} / {state.get('market')} / {state.get('as_of')}",
            f"结论: {action}，置信度 {confidence:.2f}",
            f"数据源: price={price_source}，fundamentals={fundamentals_source}，news={news_source}",
            f"风险标记: {', '.join(risk_flags) if risk_flags else '无'}",
            f"标准报告: {artifacts.get('report_path', '')}",
            f"详细报告: {artifacts.get('detail_report_path', '')}",
            f"结构化结果: {artifacts.get('final_json_path', '')}",
        ]
    )


def format_unsupported_message(resolution: dict) -> str:
    return f"已识别为 {resolution['display_name']} / {resolution['symbol']} / {resolution['market']}，但当前 MVP 仅支持 US 和 CN 市场分析。"
