from __future__ import annotations

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def parse_recommendations(ai_recommendations: list) -> list:
    result = []
    for item in ai_recommendations:
        if not isinstance(item, dict):
            continue
        priority = item.get("priority", "low")
        if priority not in _PRIORITY_ORDER:
            priority = "low"
        result.append({
            "priority": priority,
            "category": str(item.get("category", "")),
            "action": str(item.get("action", "")),
            "detail": str(item.get("detail", "")),
        })
    result.sort(key=lambda x: _PRIORITY_ORDER.get(x["priority"], 3))
    return result
