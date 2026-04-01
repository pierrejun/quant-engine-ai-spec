from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ArtifactManifest:
    job_id: str
    json_path: str
    markdown_path: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
