from sqlalchemy.orm import Session

from ..db.models import Alert, VehicleBlacklist, VehicleEvent
from ..realtime.websocket import manager


async def check_multi_camera_alert(
    db: Session,
    plate_number: str,
):
    camera_ids = (
        db.query(VehicleEvent.camera_id)
        .filter(
            VehicleEvent.plate_number.ilike(plate_number)
        )
        .distinct()
        .all()
    )

    if len(camera_ids) < 2:
        return None

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.plate_number.ilike(plate_number),
            Alert.title == "Multi-Camera Detection",
            Alert.resolved == False,
        )
        .first()
    )

    if existing_alert:
        return existing_alert

    latest_city = db.query(VehicleEvent.city).filter(VehicleEvent.plate_number.ilike(plate_number)).order_by(VehicleEvent.captured_at.desc()).scalar()
    alert = Alert(
        severity="medium",
        title="Multi-Camera Detection",
        message=(
            f"Vehicle {plate_number.upper()} detected "
            f"across {len(camera_ids)} cameras."
        ),
        plate_number=plate_number.upper(),
        resolved=False,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    await manager.broadcast(
        {
            "type": "alert",
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "plate_number": alert.plate_number,
                "resolved": alert.resolved,
                "created_at": alert.created_at.isoformat(),
                "city_name": latest_city,
            },
        }
    )

    return alert


async def check_blacklist_alert(
    db: Session,
    plate_number: str,
):
    normalized_plate = plate_number.strip().upper()
    entry = (
        db.query(VehicleBlacklist)
        .filter(VehicleBlacklist.plate_number == normalized_plate)
        .first()
    )

    if entry is None:
        return None

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.plate_number == normalized_plate,
            Alert.title == "Blacklisted Vehicle Detected",
            Alert.resolved == False,
        )
        .first()
    )

    if existing_alert:
        return existing_alert

    latest_city = db.query(VehicleEvent.city).filter(VehicleEvent.plate_number == normalized_plate).order_by(VehicleEvent.captured_at.desc()).scalar()
    alert = Alert(
        severity="high",
        title="Blacklisted Vehicle Detected",
        message=(
            f"Vehicle {normalized_plate} matched the blacklist. "
            f"Reason: {entry.reason}."
        ),
        plate_number=normalized_plate,
        resolved=False,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    await manager.broadcast(
        {
            "type": "alert",
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "plate_number": alert.plate_number,
                "resolved": alert.resolved,
                "created_at": alert.created_at.isoformat(),
                "city_name": latest_city,
            },
        }
    )

    return alert