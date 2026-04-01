from __future__ import annotations

from statistics import fmean


def _moving_average(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return fmean(values[-period:])


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema_value = fmean(values[:period])
    for value in values[period:]:
        ema_value = (value - ema_value) * multiplier + ema_value
    return ema_value


def _rsi(values: list[float], period: int = 14) -> float:
    if len(values) <= period:
        return 50.0
    gains = []
    losses = []
    for left, right in zip(values[-period - 1 : -1], values[-period:]):
        change = right - left
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _atr_pct(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float:
    if len(closes) <= period:
        return 0.0
    ranges = []
    for index in range(1, len(closes)):
        true_range = max(
            highs[index] - lows[index],
            abs(highs[index] - closes[index - 1]),
            abs(lows[index] - closes[index - 1]),
        )
        ranges.append(true_range)
    atr = fmean(ranges[-period:]) if ranges[-period:] else 0.0
    latest_close = closes[-1] or 1.0
    return atr / latest_close


def extract_technical_features(raw_data: dict) -> dict:
    history = raw_data.get("price_data", {}).get("history", [])
    closes = [item["close"] for item in history if item.get("close") is not None]
    highs = [item.get("high", item["close"]) for item in history if item.get("close") is not None]
    lows = [item.get("low", item["close"]) for item in history if item.get("close") is not None]
    ma5 = _moving_average(closes, 5)
    ma20 = _moving_average(closes, 20)
    ma60 = _moving_average(closes, 60)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = (ema12 - ema26) if ema12 is not None and ema26 is not None else 0.0
    macd_signal = "bullish" if macd > 0 else "bearish" if macd < 0 else "neutral"
    return {
        "ma5_gt_ma20": bool(ma5 and ma20 and ma5 > ma20),
        "ma20_gt_ma60": bool(ma20 and ma60 and ma20 > ma60),
        "macd_signal": macd_signal,
        "rsi14": round(_rsi(closes), 4),
        "atr_pct": round(_atr_pct(highs, lows, closes), 4),
    }
