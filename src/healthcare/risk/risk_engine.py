from __future__ import annotations


def get_risk_level(score: int | None) -> str:
    if score is None:
        return "invalid"
    if score < 50:
        return "critical"
    if score < 75:
        return "warning"
    return "normal"


def build_risk_summary(scores: dict) -> dict:
    return {metric: get_risk_level(score) for metric, score in scores.items()}


def parse_risks(ai_risks: list) -> list:
    valid_levels = {"critical", "warning", "normal", "invalid"}
    order = {"critical": 0, "warning": 1, "normal": 2, "invalid": 3}
    result = []
    for item in ai_risks:
        if not isinstance(item, dict):
            continue
        level = item.get("level", "normal")
        if level not in valid_levels:
            level = "normal"
        result.append({
            "level": level,
            "metric": str(item.get("metric", "")),
            "title": str(item.get("title", "")),
            "explanation": str(item.get("explanation", "")),
        })
    result.sort(key=lambda x: order.get(x["level"], 4))
    return result
