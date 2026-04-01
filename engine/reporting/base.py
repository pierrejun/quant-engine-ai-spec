from __future__ import annotations

from abc import ABC, abstractmethod


class BaseReportRenderer(ABC):
    @abstractmethod
    def render_markdown(self, state: dict, raw_data: dict, features: dict, evidences: list[dict], decision: dict) -> str:
        raise NotImplementedError

    @abstractmethod
    def render_detail_markdown(self, state: dict, raw_data: dict, features: dict, evidences: list[dict], decision: dict) -> str:
        raise NotImplementedError
