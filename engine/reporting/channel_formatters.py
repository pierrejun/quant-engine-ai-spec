from __future__ import annotations


def format_action(action: str) -> str:
    mapping = {
        "buy": "买入",
        "hold": "持有",
        "sell": "卖出",
        "observe": "观察",
        "insufficient_data": "数据不足",
        "hold_positive": "偏多持有",
        "hold_negative": "偏空持有",
    }
    return mapping.get(action, action.replace("_", " ").title())
