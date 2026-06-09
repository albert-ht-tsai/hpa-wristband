from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class ScoreItem(BaseModel):
    score: Optional[int] = None
    status: str  # "normal" | "warning" | "critical" | "invalid"


class ScoreBoard(BaseModel):
    total: Optional[int] = None
    sleep: ScoreItem
    heartRate: ScoreItem
    bloodPressure: ScoreItem
    bloodOxygen: ScoreItem
    bodyTemperature: ScoreItem
    hrv: ScoreItem
    ecg: ScoreItem
    met: ScoreItem
    stress: ScoreItem


class RiskItem(BaseModel):
    level: str       # "critical" | "warning" | "normal" | "invalid"
    metric: str
    title: str
    explanation: str


class RecommendationItem(BaseModel):
    priority: str    # "high" | "medium" | "low"
    category: str
    action: str
    detail: str


class HealthcareReportResponse(BaseModel):
    id: Optional[int] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    scoreBoard: ScoreBoard
    risks: List[RiskItem]
    recommendations: List[RecommendationItem]
    aiModel: str
    createdAt: datetime


class HealthcareReportListResponse(BaseModel):
    data: List[HealthcareReportResponse]
    count: int
