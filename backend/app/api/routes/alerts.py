from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Alert, VehicleEvent
from .cities import resolve_city
from ...schemas.api import AlertOut

router = APIRouter()


@router.get("", response_model=list[AlertOut])
def alerts(city: str | None = Query(default=None), city_id: str | None = Query(default=None), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    selected_city = resolve_city(db, city_id, city)
    query = db.query(Alert)
    if selected_city:
        plates = db.query(VehicleEvent.plate_number).filter(VehicleEvent.city_id == selected_city.id).distinct()
        query = query.filter(Alert.plate_number.in_(plates))
    return (
        query
        .order_by(Alert.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )