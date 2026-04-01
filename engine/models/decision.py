from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Decision:
    action: str
    confidence: float
    bullish_score: float
    bearish_score: float
    uncertainty_score: float
    data_quality_score: float
    risk_flags: list[str] = field(default_factory=list)
    top_bullish_evidence: list[str] = field(default_factory=list)
    top_bearish_evidence: list[str] = field(default_factory=list)
    internal_action: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
