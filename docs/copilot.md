# Trinetra AI Copilot

## Overview

Trinetra AI Copilot is a database-grounded investigation assistant attached to the existing FastAPI backend and dashboard. It uses authenticated access and the current `vehicle_events`, `cameras`, `vehicle_blacklist`, and `alerts` tables to answer questions such as vehicle history, last seen camera, timeline, and blacklist status.

## Required environment variables

Add these values to the project root `.env` file when needed:

```env
ADMIN_OPERATOR_ID=admin
ADMIN_ACCESS_KEY=trinetra2026
AUTH_SECRET=trinetra-local-secret
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/trinetra
CORS_ORIGINS=["http://localhost:5173"]
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
OPENAI_API_KEY=
GEMINI_API_KEY=
COPILOT_MODEL=gemini-3.6-flash
SEED_DEMO_DATA=false
```

`OPENAI_API_KEY` and `GEMINI_API_KEY` are optional. With either key configured, the assistant can format verified query results through that provider; without them, the safe database-grounded fallback remains available.
`SEED_DEMO_DATA` is disabled by default; enable it only for a local demo database.

## Backend API

Authenticated request example:

```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"Show vehicle UP32AB5698 history"}'
```

The backend:

- validates the Bearer token,
- extracts a vehicle number and optional time/camera filters,
- queries only the allowed read tables,
- returns authorized results,
- avoids fabricating missing records.

## Security notes

- Only read-only database queries are used for vehicle investigation.
- No raw SQL is executed by the LLM.
- AI-generated text is never treated as independently verified fact.
- Copilot requests are limited to 30 per client per minute.
- Missing records are answered with: `Database mein is request ke liye sufficient records available nahi hain.`

## Supported questions

- Vehicle history
- Last seen camera and timestamp
- Blacklist status
- Camera timeline
- Detection count in a time window

## Known limitations

- Real AI provider output depends on a valid API key.
- Result quality depends on available camera coverage and recorded events in the project database.
- Route reconstruction is limited to observed detections, not guaranteed full journey mapping.