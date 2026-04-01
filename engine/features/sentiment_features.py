from __future__ import annotations

from statistics import fmean


def extract_sentiment_features(raw_data: dict) -> dict:
    news_items = raw_data.get("news_data", [])
    sentiments = [float(item.get("sentiment", 0.0) or 0.0) for item in news_items]
    avg_sentiment = fmean(sentiments) if sentiments else 0.0
    volume_zscore = min(len(news_items) / 5.0, 3.0)
    return {
        "news_sentiment_3d": round(avg_sentiment, 4),
        "news_volume_zscore": round(volume_zscore, 4),
    }
