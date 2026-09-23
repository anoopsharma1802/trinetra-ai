CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE cameras(id SERIAL PRIMARY KEY,name VARCHAR(120),city VARCHAR(80) NOT NULL DEFAULT 'Unassigned',latitude DOUBLE PRECISION,longitude DOUBLE PRECISION,status VARCHAR(30) DEFAULT 'online');
CREATE TABLE vehicle_events(id BIGSERIAL PRIMARY KEY,plate_number VARCHAR(30),city VARCHAR(80) NOT NULL DEFAULT 'Unassigned',camera_id INTEGER,confidence DOUBLE PRECISION,captured_at TIMESTAMPTZ DEFAULT now(),geom GEOMETRY(Point,4326));
CREATE INDEX idx_vehicle_events_plate ON vehicle_events(plate_number);
CREATE INDEX idx_vehicle_events_geom ON vehicle_events USING GIST(geom);
