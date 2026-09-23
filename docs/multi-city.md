# Multi-city ICCC operation

## Data model

`cameras.city` and `vehicle_events.city` identify the city boundary for each observation. New ANPR events inherit the city from their camera. Existing legacy rows are migrated from camera coordinates only when they match the known Prayagraj bounds; all other unknown rows remain `Unassigned`.

## API filters

- `GET /api/v1/cities`
- `GET /api/v1/cameras?city=Prayagraj`
- `GET /api/v1/cameras?city_id=6`
- `GET /api/v1/vehicles/events?city=Prayagraj`
- `GET /api/v1/analytics/summary?city=Prayagraj`
- `GET /api/v1/vehicles/UP32AB5698/trajectory?city=Prayagraj`
- `GET /api/v1/enforcement/violations?city_id=6`

`city_id` is validated server-side and unknown or inactive IDs return HTTP 400. The legacy `city` name filter remains supported for compatibility.

The dashboard city dropdown calls these scoped endpoints, and the map recenters on the selected city's available camera coordinates.

## Production deployment

Kafka topic partitioning is intentionally not added to the MVP; the current deployment uses the existing Kafka service and database flow. For city-specific operators, add a city claim to the authenticated token and enforce it server-side in the same query filters. The current local operator token is an authenticated command-center account and does not yet carry a separate city claim.