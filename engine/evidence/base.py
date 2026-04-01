from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEvidenceBuilder(ABC):
    @abstractmethod
    def build(self, features: dict) -> list[dict]:
        raise NotImplementedError
