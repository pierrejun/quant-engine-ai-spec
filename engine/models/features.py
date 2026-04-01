from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TechnicalFeatures:
    ma5_gt_ma20: bool = False
    ma20_gt_ma60: bool = False
    macd_signal: str = "neutral"
    rsi14: float = 50.0
    atr_pct: float = 0.0


@dataclass
class ValuationFeatures:
    pe_ttm: float | None = None
    pe_percentile_3y: float | None = None
    pb_ttm: float | None = None
    pb_percentile_3y: float | None = None


@dataclass
class QualityFeatures:
    revenue_yoy: float | None = None
    net_income_yoy: float | None = None
    gross_margin_trend: float | None = None
    gross_margin_ttm: float | None = None


@dataclass
class SentimentFeatures:
    news_sentiment_3d: float = 0.0
    news_volume_zscore: float = 0.0


@dataclass
class EventFeatures:
    has_major_event: bool = False
    earnings_within_days: int | None = None


@dataclass
class FeatureSet:
    technical: TechnicalFeatures | dict[str, Any] = field(default_factory=TechnicalFeatures)
    valuation: ValuationFeatures | dict[str, Any] = field(default_factory=ValuationFeatures)
    quality: QualityFeatures | dict[str, Any] = field(default_factory=QualityFeatures)
    sentiment: SentimentFeatures | dict[str, Any] = field(default_factory=SentimentFeatures)
    event: EventFeatures | dict[str, Any] = field(default_factory=EventFeatures)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
