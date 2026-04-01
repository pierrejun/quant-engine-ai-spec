from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFeatureExtractor(ABC):
    @abstractmethod
    def extract(self, raw_data: dict) -> dict:
        raise NotImplementedError
