from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def get_price_data(self, symbol: str, market: str, as_of: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_fundamentals_data(self, symbol: str, market: str, as_of: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_news_data(self, symbol: str, market: str, as_of: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> dict:
        raise NotImplementedError
