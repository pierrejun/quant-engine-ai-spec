from __future__ import annotations

from abc import ABC, abstractmethod


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, symbol: str, market: str, as_of: str) -> dict:
        raise NotImplementedError
