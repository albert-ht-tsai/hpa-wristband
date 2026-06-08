from __future__ import annotations

import json
import os

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


def _get_health_record(db: Session, user_device_id: int, record_id: int | None) -> UserDeviceHealthRecord:
    if record_id:
        record = db.query(UserDeviceHealthRecord).filter(
            UserDeviceHealthRecord.id == record_id,
            UserDeviceHealthRecord.user_device_id == user_device_id,
        ).first()
    else:
        record = (
            db.query(UserDeviceHealthRecord)
            .filter(UserDeviceHealthRecord.user_device_id == user_device_id)
            .order_by(UserDeviceHealthRecord.created_at.desc())
            .first()
        )
    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "Health record not found"},
        )
    return record


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
        healthRecordId=report.health_record_id,
        scoreBoard=score_board,
        risks=[RiskItem(**r) for r in (report.risks or [])],
        recommendations=[RecommendationItem(**r) for r in (report.recommendations or [])],
        aiModel=report.ai_model or "",
        createdAt=report.created_at,
    )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create_healthcare_analysis(
    db: Session,
    user: User,
    user_device_id: int,
    health_record_id: int | None,
) -> UserHealthcareReport:
    _require_device(db, user, user_device_id)
    record = _get_health_record(db, user_device_id, health_record_id)

    # Step 1 – validate raw data
    validation_results = validate_health_record(record)

    # Step 2 – compute scores (deterministic)
    scores = calculate_all_scores(record)
    total = calculate_total_score(scores)
    scores["_total"] = total

    # Step 3 – derive risk levels from scores
    metric_scores = {k: v for k, v in scores.items() if k != "_total"}
    risk_levels = build_risk_summary(metric_scores)

    # Step 4 – build prompt
    prompt = build_healthcare_prompt(user, record, scores, validation_results, risk_levels)

    # Step 5 – call OpenAI
    ai_result = _call_openai(prompt)

    # Step 6 – parse & normalize AI output
    risks = parse_risks(ai_result.get("risks", []))
    recommendations = parse_recommendations(ai_result.get("recommendations", []))

    # Step 7 – persist report
    report = UserHealthcareReport(
        user_id=user.id,
        user_device_id=user_device_id,
        health_record_id=record.id,
        score_total=total,
        score_sleep=scores.get("sleep"),
        score_heart_rate=scores.get("heartRate"),
        score_blood_pressure=scores.get("bloodPressure"),
        score_blood_oxygen=scores.get("bloodOxygen"),
        score_body_temperature=scores.get("bodyTemperature"),
        score_hrv=scores.get("hrv"),
        score_ecg=scores.get("ecg"),
        score_met=scores.get("met"),
        score_stress=scores.get("stress"),
        risks=risks,
        recommendations=recommendations,
        ai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_healthcare_reports(
    db: Session,
    user: User,
    user_device_id: int,
) -> list[UserHealthcareReport]:
    _require_device(db, user, user_device_id)
    return (
        db.query(UserHealthcareReport)
        .filter(UserHealthcareReport.user_device_id == user_device_id)
        .order_by(UserHealthcareReport.created_at.desc())
        .all()
    )
