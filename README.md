# TRENETRA AI
SIH 2026 | SIH26127 | Citywide ANPR, Vehicle Trajectory Tracking & Traffic Analytics

Full-stack reference prototype: React + TypeScript + Leaflet frontend, FastAPI backend, PostgreSQL/PostGIS-ready schema, WebSocket realtime layer, and AI integration adapters for YOLO/OCR/ByteTrack/DeepSORT.

## Run
Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
Frontend: `cd frontend && npm install && npm run dev`
Docker: `docker compose up --build`

Production requires authorized camera feeds/APIs, validated models, authentication, audit/privacy controls, and deployment hardening.
