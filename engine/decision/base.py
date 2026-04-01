from __future__ import annotations

from abc import ABC, abstractmethod


class BaseDecisionEngine(ABC):
    @abstractmethod
    def decide(self, evidences: list[dict], meta: dict | None = None) -> dict:
        raise NotImplementedError
