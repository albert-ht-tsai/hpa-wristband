from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone

from dotenv import load_dotenv
from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy.orm import Session

from src.core.logging import logger
from src.healthcare.data.health_validator import validate_health_record
from src.healthcare.models.healthcare_model import UserHealthcareReport
from src.healthcare.prompt.prompt_builder import build_healthcare_prompt
from src.healthcare.recommendation.recommendation_engine import parse_recommendations
from src.healthcare.risk.risk_engine import build_risk_summary, get_risk_level, parse_risks
from src.healthcare.schemas.healthcare_schema import (
    HealthcareReportResponse,
    RecommendationItem,
    RiskItem,
    ScoreBoard,
    ScoreItem,
)
from src.healthcare.score.score_engine import calculate_all_scores, calculate_total_score
from src.user.models.user_model import User
from src.user_device.models.user_device_model import UserDevice, UserDeviceHealthRecord

load_dotenv()


# ---------------------------------------------------------------------------
# Merged health data container (duck-types UserDeviceHealthRecord attributes)
# ---------------------------------------------------------------------------

@dataclass
class MergedHealthData:
    sleep_by_day: list | None
    heart_rate: dict | None
    blood_pressure: dict | None
    blood_oxygen: dict | None
    body_temperature: dict | None
    calories: dict | None
    distance: dict | None
    met: dict | None
    stress: dict | None
    hrv: dict | None
    ecg: dict | None


def _merge_records(records: list[UserDeviceHealthRecord]) -> MergedHealthData:
    if len(records) == 1:
        r = records[0]
        return MergedHealthData(
            sleep_by_day=r.sleep_by_day,
            heart_rate=r.heart_rate,
            blood_pressure=r.blood_pressure,
            blood_oxygen=r.blood_oxygen,
            body_temperature=r.body_temperature,
            calories=r.calories,
            distance=r.distance,
            met=r.met,
            stress=r.stress,
            hrv=r.hrv,
            ecg=r.ecg,
        )

    sleep_by_day = []
    hr_slots, bp_slots, spo2_slots, temp_slots = [], [], [], []
    cal_slots, cal_total = [], 0.0
    dist_slots, dist_total = [], 0.0
    met_slots, met_steps = [], 0
    stress_slots, hrv_slots, ecg_slots = [], [], []

    for r in records:
        if r.sleep_by_day:
            sleep_by_day.extend(r.sleep_by_day)
        if r.heart_rate and r.heart_rate.get("slots"):
            hr_slots.extend(r.heart_rate["slots"])
        if r.blood_pressure and r.blood_pressure.get("slots"):
            bp_slots.extend(r.blood_pressure["slots"])
        if r.blood_oxygen and r.blood_oxygen.get("slots"):
            spo2_slots.extend(r.blood_oxygen["slots"])
        if r.body_temperature and r.body_temperature.get("slots"):
            temp_slots.extend(r.body_temperature["slots"])
        if r.calories:
            cal_slots.extend(r.calories.get("slots") or [])
            cal_total += r.calories.get("totalKcal") or 0.0
        if r.distance:
            dist_slots.extend(r.distance.get("slots") or [])
            dist_total += r.distance.get("totalKm") or 0.0
        if r.met:
            met_slots.extend(r.met.get("slots") or [])
            met_steps += r.met.get("totalSteps") or 0
        if r.stress and r.stress.get("slots"):
            stress_slots.extend(r.stress["slots"])
        if r.hrv and r.hrv.get("slots"):
            hrv_slots.extend(r.hrv["slots"])
        if r.ecg and r.ecg.get("slots"):
            ecg_slots.extend(r.ecg["slots"])

    return MergedHealthData(
        sleep_by_day=sleep_by_day or None,
        heart_rate={"slots": hr_slots} if hr_slots else None,
        blood_pressure={"slots": bp_slots} if bp_slots else None,
        blood_oxygen={"slots": spo2_slots} if spo2_slots else None,
        body_temperature={"slots": temp_slots} if temp_slots else None,
        calories={"totalKcal": round(cal_total, 2), "slots": cal_slots} if cal_slots else None,
        distance={"totalKm": round(dist_total, 3), "slots": dist_slots} if dist_slots else None,
        met={"totalSteps": met_steps, "slots": met_slots} if met_slots else None,
        stress={"slots": stress_slots} if stress_slots else None,
        hrv={"slots": hrv_slots} if hrv_slots else None,
        ecg={"slots": ecg_slots} if ecg_slots else None,
    )


# ---------------------------------------------------------------------------
# OpenAI helpers
# ---------------------------------------------------------------------------

def _get_openai_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
    )


def _call_openai(prompt: str) -> dict:
    client = _get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional health analysis AI. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error("OpenAI call failed: %s", e)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": 503, "message": f"AI service unavailable: {str(e)}"},
        )


# ---------------------------------------------------------------------------
# DB query helpers
# ---------------------------------------------------------------------------

def _require_device(db: Session, user: User, user_device_id: int) -> UserDevice:
    device = db.query(UserDevice).filter(
        UserDevice.id == user_device_id,
        UserDevice.user_id == user.id,
    ).first()
    if not device:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "Device not found"},
        )
    return device


def _get_records_in_range(
    db: Session,
    user_device_id: int,
    start_date: date,
    end_date: date,
) -> list[UserDeviceHealthRecord]:
    records = (
        db.query(UserDeviceHealthRecord)
        .filter(
            UserDeviceHealthRecord.user_device_id == user_device_id,
            UserDeviceHealthRecord.batch_date >= start_date,
            UserDeviceHealthRecord.batch_date <= end_date,
        )
        .order_by(UserDeviceHealthRecord.batch_date.asc())
        .all()
    )
    if not records:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "No health records found in the specified date range"},
        )
    return records


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def _make_score_item(score: int | None) -> ScoreItem:
    return ScoreItem(score=score, status=get_risk_level(score))


def report_to_response(report: UserHealthcareReport) -> HealthcareReportResponse:
    score_board = ScoreBoard(
        total=report.score_total,
        sleep=_make_score_item(report.score_sleep),
        heartRate=_make_score_item(report.score_heart_rate),
        bloodPressure=_make_score_item(report.score_blood_pressure),
        bloodOxygen=_make_score_item(report.score_blood_oxygen),
        bodyTemperature=_make_score_item(report.score_body_temperature),
        hrv=_make_score_item(report.score_hrv),
        ecg=_make_score_item(report.score_ecg),
        met=_make_score_item(report.score_met),
        stress=_make_score_item(report.score_stress),
    )
    return HealthcareReportResponse(
        id=report.id,
        startDate=report.start_date,
        endDate=report.end_date,
        scoreBoard=score_board,
        risks=[RiskItem(**r) for r in (report.risks or [])],
        recommendations=[RecommendationItem(**r) for r in (report.recommendations or [])],
        aiModel=report.ai_model or "",
        createdAt=report.created_at,
    )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def generate_healthcare_analysis(
    db: Session,
    user: User,
    user_device_id: int,
    start_date: date,
    end_date: date,
) -> HealthcareReportResponse:
    _require_device(db, user, user_device_id)

    # Step 1 – query health records by date range
    records = _get_records_in_range(db, user_device_id, start_date, end_date)

    # Step 2 – merge records into one analysis unit
    merged = _merge_records(records)

    # Step 3 – validate raw data
    validation_results = validate_health_record(merged)

    # Step 4 – compute scores (deterministic)
    scores = calculate_all_scores(merged)
    total = calculate_total_score(scores)
    scores["_total"] = total

    # Step 5 – derive risk levels from scores
    metric_scores = {k: v for k, v in scores.items() if k != "_total"}
    risk_levels = build_risk_summary(metric_scores)

    # Step 6 – build prompt
    prompt = build_healthcare_prompt(user, merged, scores, validation_results, risk_levels)

    # Step 7 – call OpenAI
    ai_result = _call_openai(prompt)

    # Step 8 – parse & normalize AI output
    risks = parse_risks(ai_result.get("risks", []))
    recommendations = parse_recommendations(ai_result.get("recommendations", []))

    # Step 9 – build and return response directly (no DB persistence)
    score_board = ScoreBoard(
        total=total,
        sleep=_make_score_item(scores.get("sleep")),
        heartRate=_make_score_item(scores.get("heartRate")),
        bloodPressure=_make_score_item(scores.get("bloodPressure")),
        bloodOxygen=_make_score_item(scores.get("bloodOxygen")),
        bodyTemperature=_make_score_item(scores.get("bodyTemperature")),
        hrv=_make_score_item(scores.get("hrv")),
        ecg=_make_score_item(scores.get("ecg")),
        met=_make_score_item(scores.get("met")),
        stress=_make_score_item(scores.get("stress")),
    )
    return HealthcareReportResponse(
        id=0,
        startDate=start_date,
        endDate=end_date,
        scoreBoard=score_board,
        risks=[RiskItem(**r) for r in risks],
        recommendations=[RecommendationItem(**r) for r in recommendations],
        aiModel=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        createdAt=datetime.now(timezone.utc),
    )


def get_healthcare_reports(
    db: Session,
    user: User,
    user_device_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[UserHealthcareReport]:
    _require_device(db, user, user_device_id)
    q = db.query(UserHealthcareReport).filter(
        UserHealthcareReport.user_device_id == user_device_id
    )
    if start_date:
        q = q.filter(UserHealthcareReport.start_date >= start_date)
    if end_date:
        q = q.filter(UserHealthcareReport.end_date <= end_date)
    return q.order_by(UserHealthcareReport.created_at.desc()).all()
