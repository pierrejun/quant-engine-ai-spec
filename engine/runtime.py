from __future__ import annotations

import logging.config
from pathlib import Path

from engine.collectors.composite_collector import CompositeCollector
from engine.collectors.fundamentals_collector import FundamentalsCollector
from engine.collectors.news_collector import NewsCollector
from engine.collectors.price_collector import PriceCollector
from engine.common import env_flag, load_dotenv, load_yaml
from engine.decision.decision_engine import RuleBasedDecisionEngine
from engine.evidence.builders import RuleBasedEvidenceBuilder
from engine.features.pipeline import FeaturePipeline
from engine.providers.cn.tushare_provider import TushareProvider
from engine.providers.demo import DemoProvider
from engine.providers.us.finnhub_provider import FinnhubProvider
from engine.providers.us.yahoo_provider import YahooProvider
from engine.reporting.report_renderer_v2 import MarkdownReportRenderer
from engine.risk.risk_engine import RuleBasedRiskEngine


def configure_logging(project_root: Path) -> None:
    logging_config = load_yaml(project_root / "configs" / "logging.yaml")
    logging.config.dictConfig(logging_config)


def load_runtime_config(project_root: Path) -> dict:
    return load_yaml(project_root / "configs" / "runtime.yaml")


def load_weights(project_root: Path) -> dict:
    return load_yaml(project_root / "configs" / "weights.yaml")


def load_thresholds(project_root: Path) -> dict:
    return load_yaml(project_root / "configs" / "thresholds.yaml")


def build_pipeline(project_root: Path, use_demo_data: bool | None = None) -> dict:
    load_dotenv(project_root / ".env")
    runtime_config = load_runtime_config(project_root)
    selected_demo = runtime_config["defaults"].get("use_demo_data", True) if use_demo_data is None else use_demo_data
    selected_demo = env_flag("QUANT_ENGINE_USE_DEMO_DATA", selected_demo)
    market = runtime_config["defaults"].get("market", "US").upper()

    return build_pipeline_for_market(project_root, market=market, use_demo_data=selected_demo)


def build_pipeline_for_market(project_root: Path, market: str, use_demo_data: bool = False) -> dict:
    load_dotenv(project_root / ".env")
    runtime_config = load_runtime_config(project_root)
    market = market.upper()

    if use_demo_data:
        price_provider = DemoProvider()
        fundamentals_provider = price_provider
        news_provider = price_provider
    else:
        providers_config = load_yaml(project_root / "configs" / "providers.yaml")
        if market == "US":
            yahoo_timeout = providers_config["providers"]["yahoo"].get("timeout_seconds", 10)
            finnhub_timeout = providers_config["providers"]["finnhub"].get("timeout_seconds", 10)
            yahoo_provider = YahooProvider(timeout_seconds=yahoo_timeout)
            finnhub_provider = FinnhubProvider(timeout_seconds=finnhub_timeout)
            price_provider = yahoo_provider
            fundamentals_provider = finnhub_provider
            news_provider = finnhub_provider
        elif market == "CN":
            tushare_timeout = providers_config["providers"].get("tushare", {}).get("timeout_seconds", 10)
            tushare = TushareProvider(timeout_seconds=tushare_timeout)
            price_provider = tushare
            fundamentals_provider = tushare
            news_provider = tushare
        else:
            raise ValueError(f"Unsupported market: {market}")

    collector = CompositeCollector(
        price_collector=PriceCollector(price_provider),
        fundamentals_collector=FundamentalsCollector(fundamentals_provider),
        news_collector=NewsCollector(news_provider),
    )
    return {
        "collector": collector,
        "feature_extractor": FeaturePipeline(),
        "evidence_builder": RuleBasedEvidenceBuilder(),
        "decision_engine": RuleBasedDecisionEngine(weights=load_weights(project_root), thresholds=load_thresholds(project_root)),
        "risk_engine": RuleBasedRiskEngine(thresholds=load_thresholds(project_root)),
        "report_renderer": MarkdownReportRenderer(),
        "runtime_config": runtime_config,
    }
