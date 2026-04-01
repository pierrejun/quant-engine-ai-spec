from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRiskEngine(ABC):
    @abstractmethod
    def apply(self, decision: dict, raw_data: dict, features: dict, evidences: list[dict]) -> dict:
        raise NotImplementedError
