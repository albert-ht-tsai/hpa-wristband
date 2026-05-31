from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class UserDevice(Base):
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mac_address = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    locations = relationship("UserDeviceLocation", back_populates="device", cascade="all, delete-orphan")
    health_batches = relationship("UserDeviceHealthBatch", back_populates="device", cascade="all, delete-orphan")


class UserDeviceLocation(Base):
    __tablename__ = "user_device_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_device_id = Column(Integer, ForeignKey("user_devices.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    device = relationship("UserDevice", back_populates="locations")


class UserDeviceHealthBatch(Base):
    __tablename__ = "user_device_health_batches"

    id = Column(Integer, primary_key=True, index=True)
    user_device_id = Column(Integer, ForeignKey("user_devices.id"), nullable=False, index=True)
    batch_size = Column(Integer, nullable=False)
    record_count = Column(Integer, nullable=False)
    sleep_data = Column(JSON, nullable=True)
    origin_data_3 = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    device = relationship("UserDevice", back_populates="health_batches")
