import hashlib
import re
import time
from datetime import datetime
from typing import Any, Protocol

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.models import Alert, Camera, City, StolenVehicleCheck, VehicleAuditLog, VehicleEvent, VehicleVerification

PLATE_PATTERN = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$")
_RATE_BUCKET: dict[str, list[float]] = {}


def normalize_plate(value: str) -> str:
    plate = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
    if not PLATE_PATTERN.fullmatch(plate):
        raise ValueError("Invalid registration number format")
    return plate


def _safe_reference(plate: str) -> str:
    return hashlib.sha256(f"{settings.auth_secret}:{plate}".encode()).hexdigest()[:20]


def check_rate_limit(user_id: str) -> None:
    now = time.monotonic()
    recent = [item for item in _RATE_BUCKET.get(user_id, []) if now - item < 60]
    if len(recent) >= settings.vehicle_verification_rate_limit:
        raise PermissionError("Verification request limit reached; try again shortly")
    recent.append(now)
    _RATE_BUCKET[user_id] = recent


def city_access(city_id: int | None, context: dict[str, Any]) -> None:
    allowed = context.get("city_ids", "all")
    if city_id is not None and allowed != "all" and city_id not in allowed:
        raise PermissionError("You are not authorized for this city")


class VehicleProvider(Protocol):
    async def verify(self, plate: str) -> dict[str, Any]: ...

    async def stolen_status(self, plate: str) -> dict[str, Any]: ...


class ConfiguredProvider:
    async def verify(self, plate: str) -> dict[str, Any]:
        if not settings.vahan_api_base_url or not settings.vahan_api_key:
            return {"status": "NOT_CONFIGURED", "source": "VAHAN/ULIP_NOT_CONFIGURED", "is_demo": True}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{settings.vahan_api_base_url.rstrip('/')}/vehicles/{plate}",
                    headers={"Authorization": f"Bearer {settings.vahan_api_key}"},
                )
                response.raise_for_status()
                body = response.json()
                return {
                    "status": "VERIFIED",
                    "source": "AUTHORIZED_PROVIDER",
                    "is_demo": False,
                    "vehicle_type": body.get("vehicle_type"),
                    "fuel_type": body.get("fuel_type"),
                    "registration_date": body.get("registration_date"),
                    "make_model": body.get("make_model"),
                }
        except (httpx.HTTPError, ValueError, KeyError):
            return {"status": "PROVIDER_UNAVAILABLE", "source": "AUTHORIZED_PROVIDER", "is_demo": False}

    async def stolen_status(self, plate: str) -> dict[str, Any]:
        return {"status": "NOT_CONFIGURED", "source": "POLICE_SOURCE_NOT_CONFIGURED", "is_demo": True}


class DemoProvider:
    async def verify(self, plate: str) -> dict[str, Any]:
        return {"status": "NOT_CONFIGURED", "source": "DEMO_PROVIDER", "is_demo": True}

    async def stolen_status(self, plate: str) -> dict[str, Any]:
        return {"status": "UNKNOWN", "source": "DEMO_PROVIDER", "is_demo": True}


def _provider() -> VehicleProvider:
    if settings.vahan_api_base_url and settings.vahan_api_key:
        return ConfiguredProvider()
    return DemoProvider()


class VehicleIntelligenceService:
    def __init__(self, db: Session, user_context: dict[str, Any]):
        self.db = db
        self.user_context = user_context

    def _audit(self, plate: str, action: str, result: str, city_id: int | None = None) -> str:
        record = VehicleAuditLog(
            user_id=str(self.user_context.get("sub", "unknown")),
            plate_reference=_safe_reference(plate),
            action=action,
            result_status=result,
            city_id=city_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return f"AUD-{record.id:08d}"

    def _city_for_plate(self, plate: str, city_id: int | None) -> City | None:
        if city_id is not None:
            city_access(city_id, self.user_context)
            return self.db.query(City).filter(City.id == city_id, City.is_active.is_(True)).first()
        event = self.db.query(VehicleEvent).filter(VehicleEvent.plate_number == plate).order_by(VehicleEvent.captured_at.desc()).first()
        return self.db.query(City).filter(City.id == event.city_id).first() if event and event.city_id else None

    async def verify(self, raw_plate: str, city_id: int | None = None) -> dict[str, Any]:
        plate = normalize_plate(raw_plate)
        check_rate_limit(str(self.user_context.get("sub", "unknown")))
        city = self._city_for_plate(plate, city_id)
        result = await _provider().verify(plate)
        self.db.add(VehicleVerification(
            plate_number=plate,
            provider_name=result["source"],
            verification_status=result["status"],
            response_summary="Authorized provider result stored as summary only",
            is_demo=result["is_demo"],
            requested_by=str(self.user_context.get("sub", "unknown")),
            city_id=city.id if city else city_id,
        ))
        self.db.commit()
        audit = self._audit(plate, "VEHICLE_VERIFY", result["status"], city.id if city else city_id)
        return {"plate_number": plate, "verification": result, "verified_at": datetime.utcnow().isoformat(), "audit_reference": audit}

    async def stolen_status(self, raw_plate: str, city_id: int | None = None) -> dict[str, Any]:
        plate = normalize_plate(raw_plate)
        check_rate_limit(str(self.user_context.get("sub", "unknown")))
        city = self._city_for_plate(plate, city_id)
        result = await _provider().stolen_status(plate)
        self.db.add(StolenVehicleCheck(
            plate_number=plate,
            provider_name=result["source"],
            status=result["status"],
            is_demo=result["is_demo"],
            requested_by=str(self.user_context.get("sub", "unknown")),
            city_id=city.id if city else city_id,
        ))
        self.db.commit()
        audit = self._audit(plate, "STOLEN_STATUS_CHECK", result["status"], city.id if city else city_id)
        return {"plate_number": plate, "stolen_status": result, "checked_at": datetime.utcnow().isoformat(), "audit_reference": audit}

    def history(self, plate: str, city_id: int | None = None) -> dict[str, Any]:
        city_access(city_id, self.user_context)
        query = self.db.query(VehicleEvent, Camera).join(Camera, VehicleEvent.camera_id == Camera.id).filter(VehicleEvent.plate_number == plate)
        if city_id is not None:
            query = query.filter(VehicleEvent.city_id == city_id)
        events = query.order_by(VehicleEvent.captured_at.asc()).limit(200).all()
        alerts = self.db.query(Alert).filter(Alert.plate_number == plate).order_by(Alert.created_at.desc()).limit(50).all()
        return {
            "trajectory": [{"camera_id": event.camera_id, "camera_name": camera.name, "city": event.city, "latitude": event.latitude, "longitude": event.longitude, "timestamp": event.captured_at.isoformat(), "confidence": event.confidence} for event, camera in events],
            "alerts": [{"id": alert.id, "title": alert.title, "severity": alert.severity, "status": "RESOLVED" if alert.resolved else "OPEN", "created_at": alert.created_at.isoformat()} for alert in alerts],
        }

    async def intelligence(self, raw_plate: str, city_id: int | None = None) -> dict[str, Any]:
        plate = normalize_plate(raw_plate)
        city_access(city_id, self.user_context)
        verification = await self.verify(plate, city_id)
        stolen = await self.stolen_status(plate, city_id)
        history = self.history(plate, city_id)
        return {
            "plate_number": plate,
            "vehicle_verification": verification["verification"],
            "stolen_status": stolen["stolen_status"],
            "trajectory": history["trajectory"],
            "alerts": history["alerts"],
            "verification_timestamp": verification["verified_at"],
            "audit_reference": verification["audit_reference"],
        }
