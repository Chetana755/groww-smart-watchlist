# Smart Market Watchlist

An evidence-first smart watchlist for understanding what materially changed since a user last checked. This repository currently contains Phase 0 foundations only: no watchlist, market-data, attention, event, thesis, AI, or dashboard features have been implemented.

## Prerequisites

- Docker Desktop with Docker Compose v2, or Python 3.12+ and Node.js 22+

## Start with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API health check is available at `http://localhost:8000/api/v1/health`. The Vite development server is available at `http://localhost:5173`.

## Local commands without Docker

```powershell
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .

cd ..\frontend
npm install
npm run test -- --run
npm run lint
npm run typecheck
npm run build
```

Set `DATABASE_URL` to a locally reachable PostgreSQL instance for Alembic commands. Container-local `DATABASE_URL` from `.env.example` uses the Compose service hostname.

## Migration commands

```powershell
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Documentation

- `docs/architecture.md` — boundaries and system architecture
- `docs/api-contract.md` — API conventions and planned contracts
- `docs/data-model.md` — planned persistence model
- `docs/implementation-plan.md` — approved 36-hour delivery sequence
