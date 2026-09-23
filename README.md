# TRENETRA AI
SIH 2026 | SIH26127 | Citywide ANPR, Vehicle Trajectory Tracking & Traffic Analytics

Full-stack reference prototype: React + TypeScript + Leaflet frontend, FastAPI backend, PostgreSQL/PostGIS-ready schema, WebSocket realtime layer, and AI integration adapters for YOLO/OCR/ByteTrack/DeepSORT.

## Run
Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
Frontend: `cd frontend && npm install && npm run dev`
Docker: `docker compose up --build`

## Trinetra AI Copilot

The project includes a secure vehicle investigation assistant powered by the existing database and auth layer.

- Authenticated endpoint: `POST /api/v1/copilot/chat`
- Input: `{ "message": "Show vehicle UP32AB5698 history" }`
- Response: verified database-backed answer with event records, blacklist status, and coverage notes
- If the request cannot be matched to database records, the system returns: `Database mein is request ke liye sufficient records available nahi hain.`

Optional AI provider support:

- `OPENAI_API_KEY` for OpenAI-compatible chat completion
- `COPILOT_MODEL` to override the default model

See [docs/copilot.md](docs/copilot.md) for the full setup and security notes.

## Multi-city dashboard

The dashboard provides a city selector for Lucknow, Kanpur, Varanasi, Agra, Prayagraj, and stored camera cities. City selection scopes cameras, vehicle events, analytics, trajectories, and map focus through backend database filters. Existing records in the known Prayagraj coordinate range are classified as Prayagraj; unknown records remain `Unassigned` until their camera city is configured.

Canonical city records are available from `GET /api/v1/cities`; city filters accept either a validated `city_id` or the legacy city name. Unknown city IDs return `400`. Role-specific city claims and Kafka city topics remain future deployment hardening, not simulated in local demo mode.

Production requires authorized camera feeds/APIs, validated models, authentication, audit/privacy controls, and deployment hardening.

Vehicle verification is documented in [docs/vehicle-intelligence.md](docs/vehicle-intelligence.md). It is integration-ready and demo-safe; no live VAHAN or police-source connectivity is claimed without authorized credentials and a verified provider response.
