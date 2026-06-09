from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, String

from src.core.database import Base


class UserHealthcareReport(Base):
    __tablename__ = "user_healthcare_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_device_id = Column(Integer, ForeignKey("user_devices.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True, index=True)

    score_total = Column(Integer, nullable=True)
    score_sleep = Column(Integer, nullable=True)
    score_heart_rate = Column(Integer, nullable=True)
    score_blood_pressure = Column(Integer, nullable=True)
    score_blood_oxygen = Column(Integer, nullable=True)
    score_body_temperature = Column(Integer, nullable=True)
    score_hrv = Column(Integer, nullable=True)
    score_ecg = Column(Integer, nullable=True)
    score_met = Column(Integer, nullable=True)
    score_stress = Column(Integer, nullable=True)

    risks = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)

    ai_model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
