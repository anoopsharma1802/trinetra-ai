from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import VehicleEvent, TrajectoryPoint as TrajectoryPointModel, Camera
from ...schemas.api import VehicleEventOut, TrajectoryOut, TrajectoryPoint
from ...services.alert_engine import check_multi_camera_alert

router = APIRouter()


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