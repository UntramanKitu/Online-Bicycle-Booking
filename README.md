# Bicycle Booking System Backend

FastAPI backend for Phase 3 development of the Bicycle Booking System.

Implemented modules:

- Notification Module (M13)
- Maintenance Report Module (M14)
- Feedback & Rating Module (M15)

## Requirements

- Python 3.13+
- uv
- PostgreSQL, when the team database is ready

## Setup

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and point it at a PostgreSQL database dedicated to this module set
(for example `bike_booking_m13m15_dev`), **not** the team's shared
`bike_booking_db`. M13-M15 create their own minimal `users`/`bicycles` stub
tables on startup for foreign keys; if pointed at the shared team database,
those stubs collide with the real tables from other modules (different
columns, e.g. `bicycle_name` vs. the stub's `name`) and writes fail.
Do not commit real database passwords.

```powershell
POSTGRES_DB=bike_booking_m13m15_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<local-password>
FRONTEND_ORIGIN=http://localhost:5173
```

Create the database once with `createdb bike_booking_m13m15_dev` (or via
`psql`/pgAdmin) before running the app for the first time.

## Run

```powershell
uv run uvicorn app.main:app --reload --port 8080
```

Docker Compose also uses port 8080. `start.bat` runs on port 8000 instead, which
is the frontend's default `VITE_API_BASE_URL`; if you use the command above, set
`VITE_API_BASE_URL=http://localhost:8080` in `frontend/.env`.

Open Swagger UI:

- http://127.0.0.1:8080/docs

## Project Structure

```text
app/
  main.py          # starts FastAPI, CORS, creates tables, /api/system/status
  database.py      # reads .env and connects to PostgreSQL
  models.py        # all database tables
  notification.py  # M13 Notification API
  maintenance.py   # M14 Maintenance Report API
  review.py        # M15 Feedback & Rating API
```

Each module file contains its request/response shapes and its endpoints.

## API Endpoints

### Notification (M13)

- `POST /api/notifications`
- `GET /api/notifications/user/{user_id}`
- `GET /api/notifications/{notification_id}`
- `PATCH /api/notifications/{notification_id}/read`

### Maintenance Report (M14)

- `POST /api/maintenance-reports`
- `GET /api/maintenance-reports/user/{user_id}`
- `PUT /api/maintenance-reports/{report_id}` (only while pending)
- `GET /api/maintenance-reports?status=` (admin)
- `PUT /api/maintenance-reports/{report_id}/status` (admin)

### Feedback & Rating (M15)

- `POST /api/reviews`
- `GET /api/reviews/bicycle/{bicycle_id}`
- `GET /api/reviews/bicycle/{bicycle_id}/summary`
- `GET /api/reviews/{review_id}`
- `PUT /api/reviews/{review_id}`

### System

- `GET /api/system/status`

## Integration Notes

The project includes minimal `users` and `bicycles` SQLAlchemy models only so foreign key fields can exist and the Phase 3 APIs can run before the team's full User and Bicycle modules are connected.
