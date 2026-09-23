from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import City
from ...schemas.api import CityOut

router = APIRouter()


@router.get("", response_model=list[CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(City).filter(City.is_active.is_(True)).order_by(City.name).all()


def resolve_city(db: Session, city_id: str | None, city_name: str | None = None) -> City | None:
    if city_id in (None, "", "all") and not city_name:
        return None
    if city_id not in (None, "", "all"):
        try:
            city = db.query(City).filter(City.id == int(city_id), City.is_active.is_(True)).first()
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid city_id") from error
        if city is None:
            raise HTTPException(status_code=400, detail="Unknown or inactive city")
        return city
    city = db.query(City).filter(City.name.ilike(city_name.strip()), City.is_active.is_(True)).first()
    if city is None:
        raise HTTPException(status_code=400, detail="Unknown or inactive city")
    return city
