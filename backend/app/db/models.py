from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="offline")
    stream_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


class VehicleEvent(Base):
    __tablename__ = "vehicle_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate_number: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )

    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id"),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


class VehicleBlacklist(Base):
    __tablename__ = "vehicle_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plate_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    reason: Mapped[str] = mapped_column(String(300), default="Manual review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class TrajectoryPoint(Base):
    __tablename__ = "trajectory_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate_number: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )

    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id"),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    severity: Mapped[str] = mapped_column(
        String(30),
        default="info",
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    plate_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )


class Challan(Base):
    __tablename__ = "challans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    challan_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    plate_number: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )

    violation_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    evidence_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="queued",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )