from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from engine.common import read_json


CN_CODE_PATTERN = re.compile(r"^\d{6}$")
TS_CODE_PATTERN = re.compile(r"^\d{6}\.(SH|SZ|BJ)$", re.IGNORECASE)
US_SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


@dataclass
class ResolvedSymbol:
    query: str
    symbol: str
    market: str
    display_name: str
    matched_by: str
    confidence: float
    supported: bool = True

    def model_dump(self) -> dict:
        return asdict(self)


class SymbolResolver:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.alias_config = read_json(self.project_root / "configs" / "symbol_aliases.json")
        self.alias_index = self._build_alias_index()

    def resolve(self, query: str) -> ResolvedSymbol | None:
        cleaned = self._normalize_query(query)
        if not cleaned:
            return None

        alias_hit = self.alias_index.get(cleaned.casefold())
        if alias_hit:
            return alias_hit

        upper = cleaned.upper()
        if TS_CODE_PATTERN.match(upper):
            return self._build_resolution(
                query=query,
                symbol=upper,
                market=upper.split(".")[-1].upper().replace("SH", "CN").replace("SZ", "CN").replace("BJ", "CN"),
                display_name=upper,
                matched_by="code",
                confidence=0.99,
            )

        if CN_CODE_PATTERN.match(cleaned):
            inferred_symbol = self._infer_cn_symbol(cleaned)
            if inferred_symbol:
                return self._build_resolution(
                    query=query,
                    symbol=inferred_symbol,
                    market="CN",
                    display_name=inferred_symbol,
                    matched_by="code",
                    confidence=0.92,
                )

        if US_SYMBOL_PATTERN.match(upper):
            return self._build_resolution(
                query=query,
                symbol=upper,
                market="US",
                display_name=upper,
                matched_by="code",
                confidence=0.9,
            )

        return None

    def _build_alias_index(self) -> dict[str, ResolvedSymbol]:
        index: dict[str, ResolvedSymbol] = {}
        for item in self.alias_config.get("symbols", []):
            resolution = self._build_resolution(
                query=item["display_name"],
                symbol=item["symbol"].upper(),
                market=item["market"].upper(),
                display_name=item["display_name"],
                matched_by="alias",
                confidence=0.98,
            )
            for alias in item.get("aliases", []):
                index[self._normalize_query(alias).casefold()] = resolution
            index[self._normalize_query(item["symbol"]).casefold()] = resolution
        return index

    def _build_resolution(
        self,
        query: str,
        symbol: str,
        market: str,
        display_name: str,
        matched_by: str,
        confidence: float,
    ) -> ResolvedSymbol:
        market = market.upper()
        return ResolvedSymbol(
            query=query,
            symbol=symbol.upper(),
            market=market,
            display_name=display_name,
            matched_by=matched_by,
            confidence=confidence,
            supported=market in {"US", "CN"},
        )

    def _infer_cn_symbol(self, code: str) -> str | None:
        if code.startswith(("600", "601", "603", "605", "688")):
            return f"{code}.SH"
        if code.startswith(("000", "001", "002", "003", "300", "301")):
            return f"{code}.SZ"
        if code.startswith(("430", "830", "831", "832", "833", "834", "835", "836", "837", "838", "839")):
            return f"{code}.BJ"
        return None

    def _normalize_query(self, value: str) -> str:
        return (value or "").strip().replace(" ", "")
