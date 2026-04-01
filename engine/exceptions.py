class QuantEngineError(Exception):
    """Base project exception."""


class ProviderError(QuantEngineError):
    """Raised when an upstream data provider fails."""


class CollectionError(QuantEngineError):
    """Raised when collection cannot build raw data."""


class FeatureExtractionError(QuantEngineError):
    """Raised when features cannot be extracted."""


class EvidenceBuildError(QuantEngineError):
    """Raised when evidence generation fails."""


class DecisionError(QuantEngineError):
    """Raised when a decision cannot be produced."""


class RenderError(QuantEngineError):
    """Raised when report rendering fails."""
