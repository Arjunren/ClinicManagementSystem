# Clinic Management System

A production-minded Django 6.1 and Django REST Framework API for patients, doctors, appointments, and medical records.

## Features

- Token authentication with throttled registration/login and token rotation
- Admin, receptionist, doctor, and patient roles
- Patient registration, profiles, departments, and doctor directory
- Conflict-safe appointment scheduling with ownership-scoped queries
- Guarded appointment status transitions
- Medical records restricted to assigned doctors and owning patients
- Search, ordering, pagination, structured errors, CORS allowlist, and Django admin
- PostgreSQL production configuration, SQLite local tests, Docker, and GitHub Actions

## Local setup

Requires Python 3.12+.

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
```

On macOS/Linux, activate with `source .venv/bin/activate`. Without PostgreSQL environment variables the project uses SQLite for simple local development.

Seeded credentials (development only): `admin`, `doctor`, and `patient`, each with password `ChangeMe123!`.

## API

Endpoints are under `/api/`. Authentication routes are under `/api/auth/`. The browsable API covers departments, doctors, patients, appointments, medical records, and dashboard reporting.

Authenticate by sending `Authorization: Token <token>`.

## Verification

```bash
pytest
python manage.py check
python manage.py makemigrations --check --dry-run
pip check
```

GitHub Actions repeats the suite against PostgreSQL 18.

## Docker

```bash
docker compose up --build
docker compose exec api python manage.py seed
```

The API is served at `http://localhost:8000`.

## License

MIT
