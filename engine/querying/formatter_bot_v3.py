from __future__ import annotations

ACTION_LABELS = {
    "buy": "买入",
    "hold": "观望",
    "sell": "卖出",
}

EXPLANATION_LABELS = {
    "MA5_vs_MA20": {
        "bullish": "短期趋势强于中期趋势",
        "bearish": "短期趋势弱于中期趋势",
    },
    "MACD_daily": {
        "bullish": "MACD 信号偏多",
        "bearish": "MACD 信号偏空",
        "neutral": "MACD 信号中性",
    },
    "PE_percentile_3y": {
        "bullish": "当前估值尚未进入历史高位区间",
        "bearish": "当前估值处于历史较高区间",
    },
    "Revenue_YoY": {
        "bullish": "营收增速保持为正",
        "bearish": "营收增速转为负值",
    },
    "News_sentiment_3d": {
        "bullish": "近期新闻语气整体偏正面",
        "bearish": "近期新闻语气偏中性或偏弱",
        "neutral": "近期新闻语气偏中性",
    },
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
    raw_data = result.get("raw_data") or {}
    price_data = raw_data.get("price_data") or {}
    sources = raw_data.get("sources") or {}
    evidences = result.get("evidences") or []

    action_key = decision.get("action", "未知")
    action = ACTION_LABELS.get(action_key, action_key)
    confidence = float(decision.get("confidence") or 0.0)
    risk_flags = decision.get("risk_flags") or []
    latest_close = price_data.get("latest_close")
    history = price_data.get("history") or []
    prev_close = history[-2]["close"] if len(history) >= 2 else None
    daily_change_pct = None
    if latest_close is not None and prev_close not in {None, 0}:
        daily_change_pct = ((float(latest_close) - float(prev_close)) / float(prev_close)) * 100.0

    lines = [
        _build_summary_line(action_key, state, from_cache),
        f"结论: {action}，置信度 {confidence:.2f}",
    ]
    if latest_close is not None:
        if daily_change_pct is None:
            lines.append(f"收盘价: {float(latest_close):.3f}")
        else:
            lines.append(f"收盘价: {float(latest_close):.3f}，单日涨跌幅: {daily_change_pct:+.2f}%")

    lines.append(
        f"数据源: price={sources.get('price', 'unknown')}，fundamentals={sources.get('fundamentals', 'unknown')}，news={sources.get('news', 'unknown')}"
    )
    lines.append(f"一句话建议: {_build_advice(action_key, from_cache, bool(risk_flags), state.get('as_of'))}")

    support_sentences = _factor_sentences(decision.get("top_bullish_evidence") or [], evidences)
    pressure_sentences = _factor_sentences(decision.get("top_bearish_evidence") or [], evidences)
    if support_sentences:
        lines.append(f"主要支撑: {'；'.join(support_sentences)}")
    if pressure_sentences:
        lines.append(f"主要压力: {'；'.join(pressure_sentences)}")
    lines.append(f"风险标记: {', '.join(risk_flags) if risk_flags else '无'}")
    return "\n".join(lines)


def format_followup_message(result: dict) -> str:
    state = result.get("state") or {}
    artifacts = state.get("artifacts") or {}
    symbol = state.get("symbol", "")
    return "\n".join(
        [
            f"查看报告: /report {symbol} 或 /detail {symbol}",
            f"标准报告: {artifacts.get('report_path', '')}",
            f"详细报告: {artifacts.get('detail_report_path', '')}",
            f"结构化结果: {artifacts.get('final_json_path', '')}",
        ]
    )


def format_unsupported_message(resolution: dict) -> str:
    return f"已识别为 {resolution['display_name']} / {resolution['symbol']} / {resolution['market']}，但当前 MVP 仅支持 US 和 CN 市场分析。"


def _build_summary_line(action_key: str, state: dict, from_cache: bool) -> str:
    hit_text = "缓存命中" if from_cache else "新触发"
    lead = "偏多结论" if action_key == "buy" else "偏空结论" if action_key == "sell" else "中性结论"
    return f"{lead}: {state.get('symbol')} / {state.get('market')} / {state.get('as_of')} ({hit_text})"


def _build_advice(action_key: str, from_cache: bool, has_risk_flags: bool, as_of: str | None) -> str:
    prefix = "当天已跑过，直接复用结果。" if from_cache else "这是最新生成的分析结果。"
    if action_key == "buy":
        body = "当前更偏向顺势观察做多机会，但仍建议结合仓位管理。"
    elif action_key == "sell":
        body = "当前偏空信号更强，短线更适合控制风险、谨慎追高。"
    else:
        body = "当前多空信号不够集中，继续观察会比贸然操作更稳妥。"
    if has_risk_flags:
        body += " 同时存在风险降级因素，解读时需要更保守。"
    if as_of:
        body += f" 数据日期为 {as_of}。"
    return f"{prefix}{body}"


def _factor_sentences(factors: list[str], evidences: list[dict]) -> list[str]:
    evidence_map = {item.get("factor"): item for item in evidences}
    sentences: list[str] = []
    for factor in factors:
        item = evidence_map.get(factor) or {}
        direction = item.get("direction")
        text = EXPLANATION_LABELS.get(factor, {}).get(direction)
        if not text:
            text = _sanitize_text(item.get("explanation", "")) or factor
        sentences.append(text)
    return sentences


def _sanitize_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    replacements = {
        "bullish": "偏多",
        "bearish": "偏空",
        "neutral": "中性",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned.rstrip("。?？") + "。"
