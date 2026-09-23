from datetime import datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Alert, Camera, VehicleEvent
from ...schemas.api import AnalyticsOut
from .cities import resolve_city
router = APIRouter()


@router.get('/summary', response_model=AnalyticsOut)
def summary(city: str | None = Query(default=None, max_length=80), city_id: str | None = Query(default=None), db: Session = Depends(get_db)):
	selected_city = resolve_city(db, city_id, city)
	today = datetime.utcnow().date()
	start = datetime.combine(today, time.min)
	event_query = db.query(func.count(VehicleEvent.id)).join(Camera, VehicleEvent.camera_id == Camera.id).filter(VehicleEvent.captured_at >= start)
	camera_query = db.query(func.count(Camera.id)).filter(Camera.status == 'online')
	alert_query = db.query(func.count(Alert.id)).filter(Alert.resolved.is_(False))
	if selected_city:
		event_query = event_query.filter(VehicleEvent.city_id == selected_city.id)
		camera_query = camera_query.filter(Camera.city_id == selected_city.id)
		alert_query = alert_query.filter(Alert.plate_number.in_(db.query(VehicleEvent.plate_number).filter(VehicleEvent.city_id == selected_city.id).distinct()))
	vehicles_today = event_query.scalar() or 0
	active_cameras = camera_query.scalar() or 0
	alerts_open = alert_query.scalar() or 0
	congestion_index = min(100.0, round((vehicles_today / max(active_cameras, 1)) * 2.0, 1))
	return AnalyticsOut(
		active_cameras=active_cameras,
		vehicles_today=vehicles_today,
		alerts_open=alerts_open,
		congestion_index=congestion_index,
	)


@router.get('/heatmap')
def heatmap(city: str | None = Query(default=None, max_length=80), city_id: str | None = Query(default=None), db: Session = Depends(get_db)):
	selected_city = resolve_city(db, city_id, city)
	query = db.query(
		VehicleEvent.latitude,
		VehicleEvent.longitude,
		func.count(VehicleEvent.id).label('weight'),
	)
	if selected_city:
		query = query.filter(VehicleEvent.city_id == selected_city.id)
	rows = query.group_by(VehicleEvent.latitude, VehicleEvent.longitude).all()
	maximum = max((row.weight for row in rows), default=1)
	return {
		'points': [
			{'lat': row.latitude, 'lng': row.longitude, 'weight': row.weight / maximum}
			for row in rows
		]
	}
