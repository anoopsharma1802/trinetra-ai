from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Alert, Camera, VehicleEvent
from ...schemas.api import AnalyticsOut
router = APIRouter()


@router.get('/summary', response_model=AnalyticsOut)
def summary(db: Session = Depends(get_db)):
	today = datetime.utcnow().date()
	start = datetime.combine(today, time.min)
	vehicles_today = db.query(func.count(VehicleEvent.id)).filter(
		VehicleEvent.captured_at >= start
	).scalar() or 0
	active_cameras = db.query(func.count(Camera.id)).filter(
		Camera.status == 'online'
	).scalar() or 0
	alerts_open = db.query(func.count(Alert.id)).filter(
		Alert.resolved.is_(False)
	).scalar() or 0
	congestion_index = min(100.0, round((vehicles_today / max(active_cameras, 1)) * 2.0, 1))
	return AnalyticsOut(
		active_cameras=active_cameras,
		vehicles_today=vehicles_today,
		alerts_open=alerts_open,
		congestion_index=congestion_index,
	)


@router.get('/heatmap')
def heatmap(db: Session = Depends(get_db)):
	rows = db.query(
		VehicleEvent.latitude,
		VehicleEvent.longitude,
		func.count(VehicleEvent.id).label('weight'),
	).group_by(VehicleEvent.latitude, VehicleEvent.longitude).all()
	maximum = max((row.weight for row in rows), default=1)
	return {
		'points': [
			{'lat': row.latitude, 'lng': row.longitude, 'weight': row.weight / maximum}
			for row in rows
		]
	}
