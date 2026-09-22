from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.router import api_router
from .realtime.websocket import router as ws_router

from .db.database import Base, SessionLocal, engine
from datetime import datetime, timedelta
from sqlalchemy import func

from .db.models import Alert, Camera, VehicleBlacklist, VehicleEvent

app=FastAPI(title='TRENETRA AI API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(api_router,prefix='/api/v1'); app.include_router(ws_router)


@app.on_event('startup')
def initialize_database():
	Base.metadata.create_all(bind=engine)
	db = SessionLocal()
	try:
		camera_count = db.query(Camera).count()
		if camera_count < 10:
			demo_cameras = [
				Camera(name='Civil Lines Junction', latitude=25.435, longitude=81.852, status='online'),
				Camera(name='Prayagraj Station Road', latitude=25.448, longitude=81.833, status='online'),
				Camera(name='Naini Bridge Approach', latitude=25.402, longitude=81.879, status='online'),
				Camera(name='Allahabad University Gate', latitude=25.458, longitude=81.846, status='online'),
				Camera(name='Katra Market Road', latitude=25.461, longitude=81.859, status='online'),
				Camera(name='Sangam Crossing', latitude=25.431, longitude=81.905, status='online'),
				Camera(name='Mumfordganj Signal', latitude=25.474, longitude=81.866, status='online'),
				Camera(name='George Town Main Road', latitude=25.449, longitude=81.868, status='online'),
				Camera(name='Lukerganj Flyover', latitude=25.439, longitude=81.819, status='online'),
				Camera(name='Jhunsi Checkpoint', latitude=25.417, longitude=81.960, status='online'),
			]
			db.add_all(demo_cameras[camera_count:])
		db.commit()

		cameras = db.query(Camera).order_by(Camera.id).limit(10).all()
		demo_plates = [
			'UP32AB5698', 'UP70CT2146', 'DL01AB1234', 'MH12DE1433',
			'TN10BQ1586', 'RJ14CA7788', 'KA01MN4567', 'GJ05RT9087',
			'BR01DX2468', 'WB06KQ1357',
		]
		now = datetime.utcnow()
		existing_counts = dict(
			db.query(VehicleEvent.plate_number, func.count(VehicleEvent.id))
			.group_by(VehicleEvent.plate_number)
			.all()
		)
		new_events = []
		for index, plate in enumerate(demo_plates):
			if existing_counts.get(plate, 0) >= 5:
				continue
			candidate_events = [
				VehicleEvent(
					plate_number=plate,
					camera_id=cameras[(index + point_index) % len(cameras)].id,
					confidence=0.87 + ((index + point_index) % 10) / 100,
					latitude=cameras[(index + point_index) % len(cameras)].latitude,
					longitude=cameras[(index + point_index) % len(cameras)].longitude,
					captured_at=now - timedelta(minutes=24 - index - point_index * 4),
				)
				for point_index in range(5)
			]
			new_events.extend(candidate_events[existing_counts.get(plate, 0):])
		if new_events:
			db.add_all(new_events)
			db.commit()

		if db.query(VehicleBlacklist).count() == 0:
			db.add(VehicleBlacklist(plate_number='UP32AB5698', reason='Demo watchlist vehicle'))
			db.commit()

		if db.query(Alert).count() == 0:
			db.add(Alert(
				severity='high',
				title='Blacklisted Vehicle Detected',
				message='Vehicle UP32AB5698 matched the demo watchlist.',
				plate_number='UP32AB5698',
				resolved=False,
			))
			db.commit()
	finally:
		db.close()


@app.get('/health')
def health(): return {'status':'ok','service':'trinetra-ai-backend'}
