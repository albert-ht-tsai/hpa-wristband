from __future__ import annotations
import json

METRIC_LABELS = {
    "sleep": "Sleep",
    "heartRate": "Heart Rate",
    "bloodPressure": "Blood Pressure",
    "bloodOxygen": "Blood Oxygen (SpO2)",
    "bodyTemperature": "Body Temperature",
    "hrv": "HRV (Heart Rate Variability)",
    "ecg": "ECG",
    "met": "Physical Activity (MET/Steps)",
    "stress": "Stress",
}

METRIC_KEYS = list(METRIC_LABELS.keys())


def build_healthcare_prompt(user, record, scores: dict, validation_results: dict, risk_levels: dict) -> str:
    # User profile
    profile_parts = [f"Email: {user.email}"]
    if user.name:
        profile_parts.append(f"Name: {user.name}")
    if user.age:
        profile_parts.append(f"Age: {user.age}")
    if user.sex:
        profile_parts.append(f"Sex: {user.sex}")
    if user.height:
        profile_parts.append(f"Height: {user.height} {user.height_type or 'cm'}")
    if user.weight:
        profile_parts.append(f"Weight: {user.weight} {user.weight_type or 'kg'}")
    if user.sleep_aim:
        profile_parts.append(f"Sleep Goal: {user.sleep_aim} {user.sleep_aim_type or 'hours'}")
    if user.step_aim:
        profile_parts.append(f"Daily Step Goal: {int(user.step_aim)} steps")

    profile_str = "\n".join(profile_parts)

    # Score + risk summary per metric
    metric_lines = []
    for key in METRIC_KEYS:
        label = METRIC_LABELS[key]
        score = scores.get(key)
        risk = risk_levels.get(key, "invalid")
        issues = (validation_results.get(key) or {}).get("issues", [])
        if score is None:
            metric_lines.append(f"- {label}: No valid data (INVALID)")
        else:
            issue_note = f" | Issues: {'; '.join(issues)}" if issues else ""
            metric_lines.append(f"- {label}: Score {score}/100 | Risk: {risk.upper()}{issue_note}")

    # Raw health data (compact)
    raw_data = {}
    field_map = {
        "Sleep": record.sleep_by_day,
        "HeartRate": record.heart_rate,
        "BloodPressure": record.blood_pressure,
        "BloodOxygen": record.blood_oxygen,
        "BodyTemperature": record.body_temperature,
        "HRV": record.hrv,
        "ECG": record.ecg,
        "MET": record.met,
        "Stress": record.stress,
    }
    for name, data in field_map.items():
        if data:
            raw_data[name] = data

    total = scores.get("_total", "N/A")

    return f"""You are a professional health analysis AI for a wearable health monitoring system.
Analyze the following wearable health data and return a structured JSON health report.

## User Profile
{profile_str}

## Health Score Summary (System-Computed)
Overall Score: {total}/100

{chr(10).join(metric_lines)}

## Raw Health Data
{json.dumps(raw_data, indent=2)}

## Task
Return ONLY a valid JSON object with this exact structure — no extra text or markdown:

{{
  "risks": [
    {{
      "level": "critical" | "warning" | "normal" | "invalid",
      "metric": "<one of: sleep heartRate bloodPressure bloodOxygen bodyTemperature hrv ecg met stress>",
      "title": "<concise title, max 10 words>",
      "explanation": "<clinical explanation, 1-2 sentences>"
    }}
  ],
  "recommendations": [
    {{
      "priority": "high" | "medium" | "low",
      "category": "<metric key or lifestyle>",
      "action": "<short actionable title, max 10 words>",
      "detail": "<specific guidance, 1-2 sentences>"
    }}
  ]
}}

Rules:
- Include exactly one risk entry per metric (9 total)
- Assign risk level consistent with the scores: critical < 50, warning 50-74, normal >= 75, invalid = no data
- Sort risks: critical first, warning, normal, then invalid
- Include 3 to 6 recommendations sorted by priority (high first)
- Be clinically accurate and specific to the user's data
- Return ONLY the JSON object
"""
