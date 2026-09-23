from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from ..core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_city_columns():
    inspector = inspect(engine)
    for table in ("cameras", "vehicle_events", "challans"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "city" not in columns:
            with engine.begin() as connection:
                connection.execute(text(f'ALTER TABLE {table} ADD COLUMN city VARCHAR(80)'))
        if table != "challans" and "city_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text(f'ALTER TABLE {table} ADD COLUMN city_id INTEGER'))
    with engine.begin() as connection:
        connection.execute(text("UPDATE cameras SET city = 'Unassigned' WHERE city IS NULL"))
        connection.execute(text("UPDATE vehicle_events SET city = COALESCE((SELECT city FROM cameras WHERE cameras.id = vehicle_events.camera_id), 'Unassigned') WHERE city IS NULL"))
        connection.execute(text("UPDATE cameras SET city = 'Prayagraj' WHERE city = 'Unassigned' AND latitude BETWEEN 25.30 AND 25.55 AND longitude BETWEEN 81.75 AND 82.00"))
        connection.execute(text("UPDATE vehicle_events SET city = 'Prayagraj' WHERE city = 'Unassigned' AND latitude BETWEEN 25.30 AND 25.55 AND longitude BETWEEN 81.75 AND 82.00"))
        connection.execute(text("INSERT INTO cities (name, state, country, latitude, longitude, is_active, created_at) SELECT 'Lucknow', 'Uttar Pradesh', 'India', 26.8467, 80.9462, true, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM cities WHERE name = 'Lucknow')"))
        connection.execute(text("INSERT INTO cities (name, state, country, latitude, longitude, is_active, created_at) SELECT 'Kanpur', 'Uttar Pradesh', 'India', 26.4499, 80.3319, true, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM cities WHERE name = 'Kanpur')"))
        connection.execute(text("INSERT INTO cities (name, state, country, latitude, longitude, is_active, created_at) SELECT 'Varanasi', 'Uttar Pradesh', 'India', 25.3176, 82.9739, true, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM cities WHERE name = 'Varanasi')"))
        connection.execute(text("INSERT INTO cities (name, state, country, latitude, longitude, is_active, created_at) SELECT 'Agra', 'Uttar Pradesh', 'India', 27.1767, 78.0081, true, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM cities WHERE name = 'Agra')"))
        connection.execute(text("INSERT INTO cities (name, state, country, latitude, longitude, is_active, created_at) SELECT 'Prayagraj', 'Uttar Pradesh', 'India', 25.435, 81.852, true, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM cities WHERE name = 'Prayagraj')"))
        connection.execute(text("UPDATE cameras SET city_id = (SELECT id FROM cities WHERE cities.name = cameras.city) WHERE city_id IS NULL"))
        connection.execute(text("UPDATE vehicle_events SET city_id = (SELECT id FROM cities WHERE cities.name = vehicle_events.city) WHERE city_id IS NULL"))
        connection.execute(text("UPDATE challans SET city = 'Unassigned' WHERE city IS NULL"))
