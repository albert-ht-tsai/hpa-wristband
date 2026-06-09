from __future__ import annotations

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

_MAX_SLOTS = 8  # max data points per metric sent to AI


def _avg(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


def _summarise_slots(slots: list, *keys) -> dict:
    if not slots:
        return {}
    result: dict = {"count": len(slots)}
    for k in keys:
        vals = [s.get(k) for s in slots if k in s]
        avg = _avg(vals)
        if avg is not None:
            result[f"avg_{k}"] = avg
    return result


def _build_data_summary(record) -> str:
    lines: list[str] = []

    if record.sleep_by_day:
        days = record.sleep_by_day[:_MAX_SLOTS]
        avg_total = _avg([d.get("totalMinutes") for d in days])
        avg_deep = _avg([d.get("deepMinutes") for d in days])
        avg_quality = _avg([d.get("quality") for d in days])
        lines.append(
            f"Sleep ({len(days)} days): avg_total={avg_total}min avg_deep={avg_deep}min avg_quality={avg_quality}"
        )

    if record.heart_rate:
        slots = (record.heart_rate.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "bpm")
        lines.append(f"HeartRate: {s}")

    if record.blood_pressure:
        slots = (record.blood_pressure.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "systolic", "diastolic")
        lines.append(f"BloodPressure: {s}")

    if record.blood_oxygen:
        slots = (record.blood_oxygen.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "avgPct", "minPct")
        lines.append(f"BloodOxygen: {s}")

    if record.body_temperature:
        slots = (record.body_temperature.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "avgBody", "avgSkin")
        lines.append(f"BodyTemperature: {s}")

    if record.hrv:
        slots = (record.hrv.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "value")
        lines.append(f"HRV: {s}")

    if record.ecg:
        slots = (record.ecg.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "avgValue")
        lines.append(f"ECG: {s}")

    if record.met:
        total_steps = record.met.get("totalSteps", 0)
        slots = (record.met.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "sportValue", "steps")
        s["totalSteps"] = total_steps
        lines.append(f"MET/Activity: {s}")

    if record.stress:
        slots = (record.stress.get("slots") or [])[:_MAX_SLOTS]
        s = _summarise_slots(slots, "avgLoad")
        lines.append(f"Stress: {s}")

    return "\n".join(lines) if lines else "No raw data available."


def build_healthcare_prompt(user, record, scores: dict, validation_results: dict, risk_levels: dict) -> str:
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

    profile_str = ", ".join(profile_parts)

    metric_lines = []
    for key in METRIC_KEYS:
        label = METRIC_LABELS[key]
        score = scores.get(key)
        risk = risk_levels.get(key, "invalid")
        issues = (validation_results.get(key) or {}).get("issues", [])
        if score is None:
            metric_lines.append(f"{label}: INVALID (no data)")
        else:
            issue_note = f" | {'; '.join(issues)}" if issues else ""
            metric_lines.append(f"{label}: score={score} risk={risk.upper()}{issue_note}")

    total = scores.get("_total", "N/A")
    data_summary = _build_data_summary(record)

    return f"""Health Analysis Request
User: {profile_str}
Overall Score: {total}/100

Metrics:
{chr(10).join(metric_lines)}

Data Summary:
{data_summary}

Return ONLY a JSON object:
{{"risks":[{{"level":"critical|warning|normal|invalid","metric":"<key>","title":"<max 10 words>","explanation":"<1-2 sentences>"}}],"recommendations":[{{"priority":"high|medium|low","category":"<key>","action":"<max 10 words>","detail":"<1-2 sentences>"}}]}}

Rules: 9 risk entries (one per metric), sort critical first. 3-6 recommendations sorted high priority first. Metric keys: sleep heartRate bloodPressure bloodOxygen bodyTemperature hrv ecg met stress."""
