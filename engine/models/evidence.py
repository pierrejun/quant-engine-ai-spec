from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EvidenceItem:
    factor: str
    category: str
    value: bool | float | int | str | None
    direction: str
    strength: float
    confidence: float
    source: str
    timestamp: str
    explanation: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
