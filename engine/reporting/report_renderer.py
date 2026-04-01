from __future__ import annotations

from statistics import fmean

from engine.exceptions import RenderError
from engine.reporting.base import BaseReportRenderer
from engine.reporting.channel_formatters import format_action
from engine.reporting.markdown_writer import bullet_list


class MarkdownReportRenderer(BaseReportRenderer):
    def render_markdown(self, state: dict, raw_data: dict, features: dict, evidences: list[dict], decision: dict) -> str:
        try:
            bullish = [item for item in evidences if item["direction"] == "bullish"][:3]
            bearish = [item for item in evidences if item["direction"] == "bearish"][:3]
            risks = decision.get("risk_flags", [])
            history = raw_data.get("price_data", {}).get("history", [])
            technical = features.get("technical", {})
            valuation = features.get("valuation", {})
            quality = features.get("quality", {})
            sentiment = features.get("sentiment", {})
            event = features.get("event", {})

            latest_close = history[-1]["close"] if history else None
            trailing_20 = history[-20:] if len(history) >= 20 else history
            trailing_60 = history[-60:] if len(history) >= 60 else history
            price_change_20d = self._pct_change(trailing_20[0]["close"], trailing_20[-1]["close"]) if len(trailing_20) >= 2 else None
            price_change_60d = self._pct_change(trailing_60[0]["close"], trailing_60[-1]["close"]) if len(trailing_60) >= 2 else None
            avg_volume_20d = fmean([item["volume"] for item in trailing_20]) if trailing_20 else None
            latest_volume = history[-1]["volume"] if history else None
            volume_ratio = (latest_volume / avg_volume_20d) if latest_volume is not None and avg_volume_20d not in {None, 0} else None

            return f"""# {state['symbol']} 分析报告

**分析日期**: {state.get('as_of', raw_data.get('as_of', '-'))}  
**市场**: {state.get('market', raw_data.get('market', '-'))}  
**数据来源**: price={raw_data.get('sources', {}).get('price', '-')}, fundamentals={raw_data.get('sources', {}).get('fundamentals', '-')}, news={raw_data.get('sources', {}).get('news', '-')}

## 1. 执行摘要
- 最终动作: {format_action(decision['action'])}
- 置信度: {decision['confidence']:.2f}
- 数据质量得分: {decision['data_quality_score']:.2f}
- 多头 / 空头 / 不确定性得分: {decision['bullish_score']:.2f} / {decision['bearish_score']:.2f} / {decision['uncertainty_score']:.2f}
- 核心判断: {self._build_core_view(decision, bullish, bearish)}

## 2. 市场快照
- 最新收盘价: {self._fmt_num(latest_close)}
- 近20日涨跌幅: {self._fmt_pct(price_change_20d)}
- 近60日涨跌幅: {self._fmt_pct(price_change_60d)}
- 最新成交量 / 近20日平均成交量: {self._fmt_num(latest_volume)} / {self._fmt_num(avg_volume_20d)}
- 量能比: {self._fmt_num(volume_ratio)}

## 3. 技术分析
- 趋势结构: {self._describe_trend_structure(technical)}
- 动量表现: {self._describe_momentum(technical)}
- 波动率: ATR% = {self._fmt_pct(technical.get('atr_pct'))}，波动解读 = {self._describe_volatility(technical)}
- 技术面结论: {self._build_technical_conclusion(technical, price_change_20d, price_change_60d)}

## 4. 基本面分析
- 营收同比: {self._fmt_pct(quality.get('revenue_yoy'))}
- 净利润同比: {self._fmt_pct(quality.get('net_income_yoy'))}
- 毛利率(TTM): {self._fmt_pct(quality.get('gross_margin_ttm'))}
- 基本面结论: {self._build_fundamental_conclusion(quality)}

## 5. 估值分析
- 市盈率 PE(TTM): {self._fmt_num(valuation.get('pe_ttm'))}
- PE 三年分位: {self._fmt_pct(valuation.get('pe_percentile_3y'))}
- 市净率 PB(TTM): {self._fmt_num(valuation.get('pb_ttm'))}
- PB 三年分位: {self._fmt_pct(valuation.get('pb_percentile_3y'))}
- 估值结论: {self._build_valuation_conclusion(valuation)}

## 6. 新闻与市场情绪
- 近3日新闻情绪: {self._fmt_num(sentiment.get('news_sentiment_3d'))}
- 新闻热度 Z-Score: {self._fmt_num(sentiment.get('news_volume_zscore'))}
- 重大事件标记: {self._bool_to_cn(event.get('has_major_event', False))}
- 距离财报天数: {event.get('earnings_within_days', 'N/A')}
- 情绪结论: {self._build_sentiment_conclusion(sentiment, event, raw_data)}

## 7. 证据拆解
### 偏多证据
{bullet_list([f"{item['factor']}: {item['explanation']}（强度={item['strength']:.2f}，置信度={item['confidence']:.2f}）" for item in bullish])}

### 偏空证据
{bullet_list([f"{item['factor']}: {item['explanation']}（强度={item['strength']:.2f}，置信度={item['confidence']:.2f}）" for item in bearish])}

## 8. 风险复核
- 风险标记: {", ".join(risks) if risks else "无"}
- 数据质量状态: price={raw_data.get('collection_status', {}).get('price', '-')}, fundamentals={raw_data.get('collection_status', {}).get('fundamentals', '-')}, news={raw_data.get('collection_status', {}).get('news', '-')}
- 风险结论: {self._build_risk_conclusion(decision, technical, event)}

## 9. 决策说明
- 决策原因: {self._build_decision_rationale(decision, bullish, bearish)}
- 动作映射: internal={format_action(decision.get('internal_action', '-')) if decision.get('internal_action') else '-'}，external={format_action(decision.get('action', '-'))}
- 阅读说明: 本报告为规则驱动的结构化分析结果，不构成个性化投资建议。
"""
        except Exception as exc:
            raise RenderError(str(exc)) from exc

    def _fmt_num(self, value: float | int | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f}"

    def _fmt_pct(self, value: float | int | None) -> str:
        if value is None:
            return "N/A"
        return f"{float(value) * 100:.2f}%"

    def _pct_change(self, start: float | None, end: float | None) -> float | None:
        if start in {None, 0} or end is None:
            return None
        return (end - start) / start

    def _describe_trend_structure(self, technical: dict) -> str:
        if technical.get("ma5_gt_ma20") and technical.get("ma20_gt_ma60"):
            return "短期与中期均线结构偏多，趋势排列较为健康。"
        if technical.get("ma5_gt_ma20"):
            return "短期趋势正在改善，但更大级别结构尚未完全转强。"
        if technical.get("ma20_gt_ma60"):
            return "中期结构尚可，但短期动能偏弱。"
        return "短期和中期趋势结构整体偏弱。"

    def _describe_momentum(self, technical: dict) -> str:
        macd = technical.get("macd_signal", "neutral")
        rsi = technical.get("rsi14")
        if macd == "bullish" and rsi is not None and rsi >= 55:
            return "动量偏强。"
        if macd == "bearish" and rsi is not None and rsi <= 45:
            return "动量偏弱。"
        return "动量信号偏中性或分化。"

    def _describe_volatility(self, technical: dict) -> str:
        atr_pct = technical.get("atr_pct", 0.0) or 0.0
        if atr_pct >= 0.05:
            return "较高"
        if atr_pct >= 0.03:
            return "中等"
        return "可控"

    def _build_core_view(self, decision: dict, bullish: list[dict], bearish: list[dict]) -> str:
        if decision.get("action") == "sell":
            return "当前规则体系下，偏空证据强于偏多证据。"
        if decision.get("action") == "buy":
            return "偏多证据足以覆盖当前估值与风险折减。"
        if decision.get("action") == "observe":
            return "当前确认度不足，模型更倾向先观察。"
        if decision.get("action") == "insufficient_data":
            return "当前可靠数据不足，模型无法形成高质量判断。"
        return "多空信号仍有分歧，因此模型维持持有判断。"

    def _build_technical_conclusion(self, technical: dict, price_change_20d: float | None, price_change_60d: float | None) -> str:
        if technical.get("macd_signal") == "bearish" and not technical.get("ma5_gt_ma20"):
            return "技术面仍偏弱，短期趋势尚未形成有效转强确认。"
        if technical.get("ma5_gt_ma20") and (price_change_20d or 0) > 0:
            return "价格走势有企稳迹象，短期趋势压力正在改善。"
        return "技术面信号分化，尚未体现出明确的方向优势。"

    def _build_fundamental_conclusion(self, quality: dict) -> str:
        revenue = quality.get("revenue_yoy")
        margin = quality.get("gross_margin_ttm")
        if revenue is not None and revenue > 0 and margin is not None and margin > 0:
            return "基本面增长信号具备支撑，但仍需结合估值水平和市场结构综合判断。"
        if revenue is not None and revenue > 0:
            return "营收增长为正，但更完整的质量面信息仍然有限。"
        return "当前数据截面下，基本面对结论的支撑较为有限。"

    def _build_valuation_conclusion(self, valuation: dict) -> str:
        pe_pct = valuation.get("pe_percentile_3y")
        pb_pct = valuation.get("pb_percentile_3y")
        if pe_pct is not None and pe_pct >= 0.8:
            return "相对近年的历史区间来看，当前估值偏高。"
        if pb_pct is not None and pb_pct >= 0.8:
            return "PB 所反映的估值背景同样偏贵。"
        return "从当前分位代理看，估值没有明显处于拉伸状态。"

    def _build_sentiment_conclusion(self, sentiment: dict, event: dict, raw_data: dict) -> str:
        count = len(raw_data.get("news_data", []))
        score = sentiment.get("news_sentiment_3d", 0.0) or 0.0
        if event.get("has_major_event"):
            return f"新闻流呈现事件驱动特征，最近 {count} 条信息对应的不确定性偏高。"
        if score > 0.1:
            return f"最近 {count} 条新闻的整体语气偏正面。"
        if score < -0.1:
            return f"最近 {count} 条新闻的整体语气偏负面。"
        return f"最近 {count} 条新闻整体偏中性或分化。"

    def _build_risk_conclusion(self, decision: dict, technical: dict, event: dict) -> str:
        if decision.get("risk_flags"):
            return "本次运行识别出了明确风险标记，并已据此做出解释或调整。"
        if technical.get("atr_pct", 0.0) >= 0.05:
            return "即便未触发正式降级，波动率本身也已经偏高。"
        if event.get("earnings_within_days") is not None:
            return "即使未触发降级，事件时间窗口仍值得持续跟踪。"
        return "本次未触发显式降级，但最终动作仍反映了证据平衡后的结果。"

    def _build_decision_rationale(self, decision: dict, bullish: list[dict], bearish: list[dict]) -> str:
        action = decision.get("action")
        top_bear = ", ".join(item["factor"] for item in bearish) if bearish else "none"
        top_bull = ", ".join(item["factor"] for item in bullish) if bullish else "none"
        if action == "sell":
            return f"模型之所以给出卖出，是因为偏空因素（{top_bear}）整体强于偏多支撑（{top_bull}）。"
        if action == "buy":
            return f"模型之所以给出买入，是因为偏多因素（{top_bull}）在当前结构中占优。"
        if action == "hold":
            return f"模型维持持有，是因为偏多因素（{top_bull}）与偏空因素（{top_bear}）尚未拉开决定性差距。"
        if action == "observe":
            return f"模型选择观察，是因为虽然多空两侧均有证据（{top_bull} vs {top_bear}），但确认度仍不足。"
        return "模型判断为数据不足，原因是当前证据不完整或整体置信度不够。"

    def _bool_to_cn(self, value: bool) -> str:
        return "是" if value else "否"
