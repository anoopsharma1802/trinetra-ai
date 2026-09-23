from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Challan
from .cities import resolve_city

router = APIRouter()


class ChallanRequest(BaseModel):
    plate_number: str
    violation_code: str
    location: str
    evidence_url: str | None = None
    city: str | None = None


@router.get("/violations")
def violations(city: str | None = Query(default=None), city_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    selected_city = resolve_city(db, city_id, city)
    query = db.query(Challan)
    if selected_city:
        query = query.filter(Challan.city == selected_city.name)
    return query.order_by(Challan.created_at.desc()).limit(200).all()


@router.post("/challan")
def challan(
    payload: ChallanRequest,
    db: Session = Depends(get_db),
):
    challan_number = (
        f"TRN-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    )

    challan_record = Challan(
        challan_number=challan_number,
        plate_number=payload.plate_number,
        violation_code=payload.violation_code,
        location=payload.location,
        city=payload.city,
        evidence_url=payload.evidence_url,
        status="queued",
    )

    db.add(challan_record)
    db.commit()
    db.refresh(challan_record)

    return {
        "status": "queued",
        "message": "Demo enforcement workflow accepted",
        "challan_number": challan_record.challan_number,
        "plate_number": challan_record.plate_number,
        "violation_code": challan_record.violation_code,
        "location": challan_record.location,
        "evidence_url": challan_record.evidence_url,
        "created_at": challan_record.created_at,
    }