from __future__ import annotations


def _in_range(value, lo, hi) -> bool:
    return lo <= value <= hi


def _validate_slots(data: dict | None, field_ranges: dict) -> dict:
    if not data:
        return {"valid": False, "issues": ["no data"]}
    slots = data.get("slots") or []
    if not slots:
        return {"valid": False, "issues": ["empty slots"]}
    issues = []
    for i, slot in enumerate(slots):
        for field, (lo, hi) in field_ranges.items():
            val = slot.get(field)
            if val is not None and not _in_range(val, lo, hi):
                issues.append(f"slot[{i}].{field}={val} out of range [{lo}, {hi}]")
    return {"valid": len(issues) == 0, "issues": issues}


def validate_health_record(record) -> dict:
    """
    Returns {metric: {"valid": bool, "issues": [str]}}.
    """
    results = {}

    # Sleep
    sleep_data = record.sleep_by_day
    if sleep_data:
        issues = []
        for i, day in enumerate(sleep_data):
            tm = day.get("totalMinutes")
            q = day.get("quality")
            if tm is not None and not _in_range(tm, 0, 960):
                issues.append(f"day[{i}].totalMinutes={tm} out of range [0, 960]")
            if q is not None and not _in_range(q, 0, 100):
                issues.append(f"day[{i}].quality={q} out of range [0, 100]")
        results["sleep"] = {"valid": len(issues) == 0, "issues": issues}
    else:
        results["sleep"] = {"valid": False, "issues": ["no data"]}

    results["heartRate"] = _validate_slots(record.heart_rate, {"bpm": (30, 220)})
    results["bloodPressure"] = _validate_slots(
        record.blood_pressure, {"systolic": (60, 250), "diastolic": (40, 160)}
    )
    results["bloodOxygen"] = _validate_slots(
        record.blood_oxygen, {"avgPct": (80, 100), "minPct": (70, 100), "maxPct": (80, 100)}
    )
    results["bodyTemperature"] = _validate_slots(
        record.body_temperature, {"avgBody": (34.0, 42.0), "avgSkin": (20.0, 42.0)}
    )
    results["hrv"] = _validate_slots(record.hrv, {"value": (1.0, 300.0)})
    results["ecg"] = _validate_slots(record.ecg, {"avgValue": (0.0, 2000.0)})
    results["stress"] = _validate_slots(record.stress, {"avgLoad": (0, 100)})

    # MET
    met = record.met
    if not met:
        results["met"] = {"valid": False, "issues": ["no data"]}
    else:
        issues = []
        ts = met.get("totalSteps")
        if ts is not None and not _in_range(ts, 0, 200000):
            issues.append(f"totalSteps={ts} out of range [0, 200000]")
        results["met"] = {"valid": len(issues) == 0, "issues": issues}

    return results
