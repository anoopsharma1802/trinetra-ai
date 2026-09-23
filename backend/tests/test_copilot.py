from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.db.models import Camera, VehicleBlacklist, VehicleEvent
from app.api.routes.auth import create_access_token


def build_client_with_seeded_data():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        camera = Camera(name="Civil Lines Junction", latitude=25.435, longitude=81.852, status="online")
        session.add(camera)
        session.flush()

        session.add_all(
            [
                VehicleEvent(
                    plate_number="UP32AB5698",
                    camera_id=camera.id,
                    confidence=0.94,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    captured_at=datetime.utcnow() - timedelta(minutes=15),
                ),
                VehicleEvent(
                    plate_number="UP32AB5698",
                    camera_id=camera.id,
                    confidence=0.91,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    captured_at=datetime.utcnow() - timedelta(minutes=5),
                ),
                VehicleEvent(
                    plate_number="UP70CT2146",
                    camera_id=camera.id,
                    confidence=0.88,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    captured_at=datetime.utcnow() - timedelta(minutes=2),
                ),
            ]
        )
        session.add(VehicleBlacklist(plate_number="UP32AB5698", reason="Demo watchlist vehicle"))
        session.commit()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    token = create_access_token("admin")
    return client, token


def test_vehicle_history_service_returns_events():
    client, token = build_client_with_seeded_data()

    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Show vehicle UP32AB5698 history"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["vehicle_number"] == "UP32AB5698"
    assert len(payload["data"]["events"]) >= 2


def test_copilot_route_rejects_invalid_auth():
    client, _ = build_client_with_seeded_data()

    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Show vehicle UP32AB5698 history"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
