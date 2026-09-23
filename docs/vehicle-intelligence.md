# Vehicle Intelligence

## Status

The vehicle intelligence module is **INTEGRATION READY**. It does not claim live VAHAN, ULIP, NCRB, ZIPNET, or police connectivity unless an authorized provider base URL and credential are configured and tested.

Without an authorized provider, responses are explicitly marked `DEMO`/`NOT_CONFIGURED` and contain no fabricated owner or government records.

## Endpoints

The existing API prefix is `/api/v1`:

- `GET /api/v1/vehicles/{plate_number}/verify`
- `GET /api/v1/vehicles/{plate_number}/stolen-status`
- `GET /api/v1/vehicles/{plate_number}/intelligence`

All endpoints require the existing Bearer token.

## Configuration

Use placeholders only in documentation and keep real values in the local `.env` file:

```env
VAHAN_API_BASE_URL=https://authorized-provider.example/api
VAHAN_API_KEY=<authorized-secret>
VAHAN_PROVIDER_MODE=authorized
STOLEN_PROVIDER_MODE=not_configured
VEHICLE_VERIFICATION_RATE_LIMIT=30
```

The current local project uses demo-safe fallback mode unless an authorized VAHAN-compatible endpoint is configured. Stolen-vehicle status remains `UNKNOWN` or `NOT_CONFIGURED` until an authorized police/NCRB/ZIPNET/state-police provider is integrated.

## Safety

- Registration numbers are normalized and validated.
- Provider keys never go to the frontend or audit logs.
- Audit records store a keyed hash reference, not the raw plate.
- Responses do not expose owner address, chassis number, engine number, or raw provider payloads.
- `DEMO_MATCH` must never be interpreted as a police or government stolen-vehicle finding.
- Existing city filters can be supplied using `city_id` and are checked against token context.

## macOS / VS Code

Docker path:

```bash
cd /Users/apple/trinetra-ai
docker compose up --build -d
curl http://localhost:8000/health
```

The frontend is at `http://localhost:5173`. Authenticate in the dashboard with the configured local operator, then open **Live Vehicle Tracking** and use **VERIFY VEHICLE**.

Backend checks:

```bash
docker compose exec -T backend python -m compileall -q app
docker compose config --quiet
docker compose logs --tail=100 backend
```

The core Docker image intentionally does not install the optional full ANPR/OCR profile because it pulls large CPU/CUDA ML dependencies. The profile is available in `backend/requirements-anpr.txt` for a dedicated ML environment; model weights are still required separately and no model file is fabricated by the project.

Local development, if dependencies are installed:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another VS Code terminal:

```bash
cd frontend
npm install
npm run dev
```

## Limitations

The current local authentication token is a `SUPER_ADMIN` demo command-center token. Separate city operator accounts and provider-specific police integrations require authorized identities and contracts; they are not simulated.
