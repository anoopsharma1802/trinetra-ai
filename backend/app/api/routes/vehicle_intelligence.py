from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...services.vehicle_intelligence import VehicleIntelligenceService
from .auth import token_context

router = APIRouter()


def service_for(authorization: str | None, db: Session) -> VehicleIntelligenceService:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    context = token_context(authorization.split(" ", 1)[1].strip())
    if not context:
        raise HTTPException(status_code=401, detail="Authentication required")
    return VehicleIntelligenceService(db, context)


@router.get("/{plate_number}/verify")
async def verify_vehicle(
    plate_number: str,
    city_id: int | None = Query(default=None, ge=1),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    try:
        return await service_for(authorization, db).verify(plate_number, city_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get("/{plate_number}/stolen-status")
async def stolen_status(
    plate_number: str,
    city_id: int | None = Query(default=None, ge=1),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    try:
        return await service_for(authorization, db).stolen_status(plate_number, city_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get("/{plate_number}/intelligence")
async def intelligence(
    plate_number: str,
    city_id: int | None = Query(default=None, ge=1),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    try:
        return await service_for(authorization, db).intelligence(plate_number, city_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
