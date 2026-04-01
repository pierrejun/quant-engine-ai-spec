from __future__ import annotations

from engine.exceptions import FeatureExtractionError
from engine.features.base import BaseFeatureExtractor
from engine.features.event_features import extract_event_features
from engine.features.quality_features import extract_quality_features
from engine.features.sentiment_features import extract_sentiment_features
from engine.features.technical_features import extract_technical_features
from engine.features.valuation_features import extract_valuation_features
from engine.models.features import FeatureSet


class FeaturePipeline(BaseFeatureExtractor):
    def extract(self, raw_data: dict) -> dict:
        try:
            features = FeatureSet(
                technical=extract_technical_features(raw_data),
                valuation=extract_valuation_features(raw_data),
                quality=extract_quality_features(raw_data),
                sentiment=extract_sentiment_features(raw_data),
                event=extract_event_features(raw_data),
            )
            return features.model_dump()
        except Exception as exc:
            raise FeatureExtractionError(str(exc)) from exc
