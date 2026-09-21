from datetime import datetime

from sqlalchemy.orm import Session

from ..db.models import VehicleEvent


def save_anpr_detection(
    db: Session,
    plate_number: str,
    camera_id: int,
    confidence: float,
    latitude: float,
    longitude: float,
    image_url: str | None = None,
):
    """
    Save a validated ANPR detection into vehicle_events.
    """

    event = VehicleEvent(
        plate_number=plate_number.upper().strip(),
        camera_id=camera_id,
        confidence=float(confidence),
        latitude=float(latitude),
        longitude=float(longitude),
        captured_at=datetime.utcnow(),
        image_url=image_url,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event