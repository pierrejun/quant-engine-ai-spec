from __future__ import annotations

from datetime import UTC, datetime

from engine.evidence.base import BaseEvidenceBuilder
from engine.evidence.weighting import clamp
from engine.exceptions import EvidenceBuildError
from engine.models.evidence import EvidenceItem


class RuleBasedEvidenceBuilder(BaseEvidenceBuilder):
    def build(self, features: dict) -> list[dict]:
        try:
            timestamp = datetime.now(UTC).date().isoformat()
            evidence: list[EvidenceItem] = []
            technical = features["technical"]
            valuation = features["valuation"]
            quality = features["quality"]
            sentiment = features["sentiment"]
            event = features["event"]

            evidence.append(
                EvidenceItem(
                    factor="MA5_vs_MA20",
                    category="technical",
                    value=technical["ma5_gt_ma20"],
                    direction="bullish" if technical["ma5_gt_ma20"] else "bearish",
                    strength=0.62 if technical["ma5_gt_ma20"] else 0.38,
                    confidence=0.91,
                    source="price",
                    timestamp=timestamp,
                    explanation="短期趋势强于中期趋势。" if technical["ma5_gt_ma20"] else "短期趋势弱于中期趋势。",
                )
            )
            evidence.append(
                EvidenceItem(
                    factor="MACD_daily",
                    category="technical",
                    value=technical["macd_signal"],
                    direction="bullish" if technical["macd_signal"] == "bullish" else "bearish" if technical["macd_signal"] == "bearish" else "neutral",
                    strength=0.58 if technical["macd_signal"] == "bullish" else 0.42 if technical["macd_signal"] == "bearish" else 0.50,
                    confidence=0.82,
                    source="price",
                    timestamp=timestamp,
                    explanation=f"MACD 信号为 {technical['macd_signal']}。",
                )
            )
            if valuation["pe_percentile_3y"] is not None:
                bearish = valuation["pe_percentile_3y"] >= 0.65
                evidence.append(
                    EvidenceItem(
                        factor="PE_percentile_3y",
                        category="fundamentals",
                        value=valuation["pe_percentile_3y"],
                        direction="bearish" if bearish else "bullish",
                        strength=clamp(abs(valuation["pe_percentile_3y"] - 0.5) + 0.2),
                        confidence=0.76,
                        source="fundamentals",
                        timestamp=timestamp,
                        explanation="当前估值处于历史较高区间。" if bearish else "当前估值尚未进入历史高位区间。",
                    )
                )
            if quality["revenue_yoy"] is not None:
                positive = quality["revenue_yoy"] > 0
                evidence.append(
                    EvidenceItem(
                        factor="Revenue_YoY",
                        category="fundamentals",
                        value=quality["revenue_yoy"],
                        direction="bullish" if positive else "bearish",
                        strength=clamp(abs(quality["revenue_yoy"]) + 0.3),
                        confidence=0.85,
                        source="fundamentals",
                        timestamp=timestamp,
                        explanation="营收增速保持为正。" if positive else "营收增速转为负值。",
                    )
                )
            evidence.append(
                EvidenceItem(
                    factor="News_sentiment_3d",
                    category="sentiment",
                    value=sentiment["news_sentiment_3d"],
                    direction="bullish" if sentiment["news_sentiment_3d"] > 0.05 else "bearish" if sentiment["news_sentiment_3d"] < -0.05 else "neutral",
                    strength=clamp(abs(sentiment["news_sentiment_3d"]) + 0.2),
                    confidence=0.70,
                    source="news",
                    timestamp=timestamp,
                    explanation="近期新闻语气整体偏正面。" if sentiment["news_sentiment_3d"] > 0.05 else "近期新闻语气偏中性或偏弱。",
                )
            )
            if event["has_major_event"]:
                evidence.append(
                    EvidenceItem(
                        factor="Major_event_flag",
                        category="sentiment",
                        value=True,
                        direction="bearish",
                        strength=0.60,
                        confidence=0.65,
                        source="news",
                        timestamp=timestamp,
                        explanation="事件扰动增强了不确定性。",
                    )
                )
            return [item.model_dump() for item in evidence]
        except Exception as exc:
            raise EvidenceBuildError(str(exc)) from exc
