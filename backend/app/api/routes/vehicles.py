from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import VehicleBlacklist, VehicleEvent, TrajectoryPoint as TrajectoryPointModel, Camera
from ...schemas.api import VehicleBlacklistIn, VehicleBlacklistOut, VehicleEventOut, TrajectoryOut, TrajectoryPoint
from ...services.alert_engine import check_multi_camera_alert

router = APIRouter()


@router.get("/blacklist", response_model=list[VehicleBlacklistOut])
def blacklist(db: Session = Depends(get_db)):
    return db.query(VehicleBlacklist).order_by(VehicleBlacklist.created_at.desc()).all()


@router.post("/blacklist", response_model=VehicleBlacklistOut, status_code=201)
def add_to_blacklist(payload: VehicleBlacklistIn, db: Session = Depends(get_db)):
    plate_number = payload.plate_number.strip().upper()
    reason = payload.reason.strip() or "Manual review"

    if not plate_number:
        raise HTTPException(status_code=400, detail="Vehicle number is required")

    existing = db.query(VehicleBlacklist).filter(VehicleBlacklist.plate_number == plate_number).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vehicle is already blacklisted")

    entry = VehicleBlacklist(plate_number=plate_number, reason=reason)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/blacklist/{plate_number}")
def remove_from_blacklist(plate_number: str, db: Session = Depends(get_db)):
    entry = db.query(VehicleBlacklist).filter(
        VehicleBlacklist.plate_number == plate_number.strip().upper()
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Vehicle is not blacklisted")

    db.delete(entry)
    db.commit()
    return {"status": "removed", "plate_number": plate_number.strip().upper()}


@router.get("/events", response_model=list[VehicleEventOut])
def events(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(VehicleEvent)
        .order_by(VehicleEvent.captured_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{plate_number}/trajectory", response_model=TrajectoryOut)
def trajectory(
    plate_number: str,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(VehicleEvent, Camera)
        .join(Camera, VehicleEvent.camera_id == Camera.id)
        .filter(VehicleEvent.plate_number.ilike(plate_number))
        .order_by(VehicleEvent.captured_at.asc())
        .all()
    )

    points = [
        TrajectoryPoint(
            camera_id=event.camera_id,
            camera_name=camera.name,
            latitude=event.latitude,
            longitude=event.longitude,
            timestamp=event.captured_at,
            confidence=event.confidence,
        )
        for event, camera in rows
    ]

    return TrajectoryOut(
        plate_number=plate_number.upper(),
        points=points,
    )


@router.post("/events/test/{plate_number}")
async def test_vehicle_event(
    plate_number: str,
    db: Session = Depends(get_db),
):
    alert = await check_multi_camera_alert(
        db,
        plate_number,
    )

    if alert:
        return {
            "status": "alert_created",
            "alert_id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "plate_number": alert.plate_number,
        }

    return {
        "status": "no_alert",
        "plate_number": plate_number.upper(),
        "message": "Multi-camera rule was not triggered.",
    }