from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Challan

router = APIRouter()


class ChallanRequest(BaseModel):
    plate_number: str
    violation_code: str
    location: str
    evidence_url: str | None = None


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