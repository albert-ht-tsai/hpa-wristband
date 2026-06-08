from __future__ import annotations


def _avg(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def score_sleep(sleep_by_day: list | None) -> int | None:
    if not sleep_by_day:
        return None
    qualities = [d.get("quality") for d in sleep_by_day if d.get("quality") is not None]
    minutes_list = [d.get("totalMinutes") for d in sleep_by_day if d.get("totalMinutes") is not None]
    if not qualities and not minutes_list:
        return None

    avg_quality = _avg(qualities) if qualities else 50.0
    avg_min = _avg(minutes_list) if minutes_list else 0.0

    if 420 <= avg_min <= 540:
        dur = 100
    elif 360 <= avg_min < 420 or 540 < avg_min <= 600:
        dur = 75
    elif 300 <= avg_min < 360 or 600 < avg_min <= 660:
        dur = 50
    else:
        dur = 25

    return int(avg_quality * 0.5 + dur * 0.5)


def score_heart_rate(heart_rate: dict | None) -> int | None:
    if not heart_rate:
        return None
    slots = heart_rate.get("slots") or []
    bpms = [s.get("bpm") for s in slots if s.get("bpm") is not None]
    if not bpms:
        return None
    avg = _avg(bpms)
    if 60 <= avg <= 100:
        return 100
    if 50 <= avg < 60 or 100 < avg <= 110:
        return 75
    if 40 <= avg < 50 or 110 < avg <= 130:
        return 50
    return 25


def score_blood_pressure(blood_pressure: dict | None) -> int | None:
    if not blood_pressure:
        return None
    slots = blood_pressure.get("slots") or []
    sys_vals = [s.get("systolic") for s in slots if s.get("systolic") is not None]
    dia_vals = [s.get("diastolic") for s in slots if s.get("diastolic") is not None]
    if not sys_vals or not dia_vals:
        return None
    avg_sys = _avg(sys_vals)
    avg_dia = _avg(dia_vals)
    if avg_sys < 120 and avg_dia < 80:
        return 100
    if avg_sys < 130 and avg_dia < 80:
        return 80
    if avg_sys < 140 or avg_dia < 90:
        return 55
    return 30


def score_blood_oxygen(blood_oxygen: dict | None) -> int | None:
    if not blood_oxygen:
        return None
    slots = blood_oxygen.get("slots") or []
    vals = [s.get("avgPct") for s in slots if s.get("avgPct") is not None]
    if not vals:
        return None
    avg = _avg(vals)
    if avg >= 97:
        return 100
    if avg >= 95:
        return 75
    if avg >= 90:
        return 50
    return 25


def score_body_temperature(body_temperature: dict | None) -> int | None:
    if not body_temperature:
        return None
    slots = body_temperature.get("slots") or []
    vals = [s.get("avgBody") for s in slots if s.get("avgBody") is not None]
    if not vals:
        return None
    avg = _avg(vals)
    if 36.1 <= avg <= 37.2:
        return 100
    if 37.2 < avg <= 37.8 or 35.5 <= avg < 36.1:
        return 75
    if 37.8 < avg <= 38.5 or 35.0 <= avg < 35.5:
        return 50
    return 25


def score_hrv(hrv: dict | None) -> int | None:
    if not hrv:
        return None
    slots = hrv.get("slots") or []
    vals = [s.get("value") for s in slots if s.get("value") is not None]
    if not vals:
        return None
    avg = _avg(vals)
    if avg >= 60:
        return 100
    if avg >= 40:
        return 75
    if avg >= 20:
        return 50
    return 25


def score_ecg(ecg: dict | None) -> int | None:
    if not ecg:
        return None
    slots = ecg.get("slots") or []
    vals = [s.get("avgValue") for s in slots if s.get("avgValue") is not None]
    if not vals:
        return None
    avg = _avg(vals)
    if 400 <= avg <= 600:
        return 90
    if 300 <= avg < 400 or 600 < avg <= 700:
        return 65
    return 40


def score_met(met: dict | None) -> int | None:
    if not met:
        return None
    steps = met.get("totalSteps")
    if steps is None or steps == 0:
        return None
    if steps >= 10000:
        return 100
    if steps >= 7500:
        return 80
    if steps >= 5000:
        return 60
    if steps >= 2500:
        return 40
    return 20


def score_stress(stress: dict | None) -> int | None:
    if not stress:
        return None
    slots = stress.get("slots") or []
    vals = [s.get("avgLoad") for s in slots if s.get("avgLoad") is not None]
    if not vals:
        return None
    avg = _avg(vals)
    if avg <= 25:
        return 100
    if avg <= 50:
        return 75
    if avg <= 75:
        return 50
    return 25


def calculate_all_scores(record) -> dict:
    return {
        "sleep": score_sleep(record.sleep_by_day),
        "heartRate": score_heart_rate(record.heart_rate),
        "bloodPressure": score_blood_pressure(record.blood_pressure),
        "bloodOxygen": score_blood_oxygen(record.blood_oxygen),
        "bodyTemperature": score_body_temperature(record.body_temperature),
        "hrv": score_hrv(record.hrv),
        "ecg": score_ecg(record.ecg),
        "met": score_met(record.met),
        "stress": score_stress(record.stress),
    }


def calculate_total_score(scores: dict) -> int | None:
    valid = [v for v in scores.values() if v is not None]
    if not valid:
        return None
    return int(sum(valid) / len(valid))
