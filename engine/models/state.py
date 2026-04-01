from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AnalysisArtifacts:
    raw_snapshot_path: str = ""
    features_path: str = ""
    evidence_path: str = ""
    decision_path: str = ""
    report_path: str = ""
    detail_report_path: str = ""
    final_json_path: str = ""


@dataclass
class AnalysisState:
    job_id: str
    symbol: str
    market: str
    as_of: str
    status: str = "pending"
    stage: str = "pending"
    started_at: str = ""
    updated_at: str = ""
    data_quality: dict[str, str] = field(default_factory=dict)
    artifacts: AnalysisArtifacts = field(default_factory=AnalysisArtifacts)
    errors: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
