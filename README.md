
# Smart Market Watchlist

> **A normal watchlist tells you what your stocks are doing. Smart Watchlist tells you what you missed.**

Smart Market Watchlist is a context-aware market watchlist designed to reduce attention overload.

Instead of showing every price movement, it identifies **meaningful changes**, explains why they matter, remembers what the user has already seen, and surfaces only genuinely new developments.

## What makes it different?

Traditional watchlists answer:

> "How are my stocks doing?"

Smart Watchlist answers:

> **"What changed since I last checked, why did it change, and does it matter?"**

### Core capabilities

- **Meaningful-change detection** using a deterministic attention engine
- **Evidence-first explanations** for every important movement
- **Last-seen state** to distinguish new changes from already-seen changes
- **Market and sector context** for relative movement
- **Volume anomaly detection**
- **Corporate-event context**
- **Data-quality awareness** for fresh, delayed, stale and conflicting data
- **Persistent watchlists** with add, remove and reorder support
- **Deterministic demo scenarios** for reproducible evaluation
- **Provider abstraction** designed for integration with real market-data providers

## Example

A company moves +5.5%.

Instead of simply displaying:

`TCS +5.5%`

the system explains:

- Price moved +5.5%
- Volume is 3.2× average
- Moved 5.1% relative to sector
- Relevant company event detected

The attention engine combines these signals to determine whether the movement deserves the user's attention.

## "What did I miss?"

The system maintains a `last_market_check_at` timestamp.

This allows it to distinguish between:

- **Important but already seen**
- **Important and NEW**
- **No meaningful change**

For example:

```text
Company Move
    ↓
TCS +4.2%
    ↓
User checks the dashboard
    ↓
Marked as seen
    ↓
Refresh
    ↓
0 new meaningful changes
    ↓
NEW_UPDATE occurs
    ↓
TCS +5.5%
    ↓
1 NEW meaningful change
````

## Architecture

```text
React + TypeScript + Vite
            |
        Typed API
            |
          FastAPI
            |
    +-------+-------+
    |       |       |
  Domain Services Providers
    |       |       |
    +-------+-------+
            |
       PostgreSQL
```

### Backend structure

* `api/` — HTTP endpoints and request/response handling
* `services/` — application use cases
* `domain/` — deterministic attention and business logic
* `providers/` — market-data provider abstraction and demo provider
* `repositories/` — persistence operations
* `models/` — SQLAlchemy models
* `schemas/` — Pydantic API contracts

The attention engine is deterministic and does not rely on an LLM to decide whether a market movement is significant.

## Demo Market Feed

The prototype uses deterministic market-data scenarios so that the same behavior can be reproduced during evaluation.

Available scenarios include:

* Normal day
* Company move
* Sector move
* Unusual volume
* Mixed signals
* Stale data
* Conflicting data
* NEW_UPDATE

The architecture separates the market-data provider from the attention engine, allowing a licensed real-time market-data provider to be integrated without changing the core decision logic.

## Tech Stack

### Frontend

* React
* TypeScript
* Vite

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

### Database

* PostgreSQL

### Infrastructure

* Docker
* Docker Compose
* Railway
* Neon PostgreSQL

## Running locally

### Prerequisites

* Docker Desktop
* Docker Compose

### Start the application

```bash
git clone https://github.com/Chetana755/groww-smart-watchlist.git
cd groww-smart-watchlist
docker compose up --build
```

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/v1/health
```

## Production Demo

Frontend:

[https://groww-smart-watchlist-production-ae45.up.railway.app/](https://groww-smart-watchlist-production-ae45.up.railway.app/)

Backend:

[https://groww-smart-watchlist-production.up.railway.app/](https://groww-smart-watchlist-production.up.railway.app/)

## Testing

Backend:

```bash
cd backend
pytest
ruff check .
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Project Documentation

* `docs/architecture.md` — system architecture and boundaries
* `docs/api-contract.md` — API conventions
* `docs/data-model.md` — persistence model
* `docs/implementation-plan.md` — implementation plan

## Hackathon

Built for **CODE 2026 — Groww Smart Market Watchlist Challenge**.

The focus is on:

* Product interpretation
* Engineering depth
* Resilience and edge cases
* Code quality and simplicity
* Originality and thoughtful design

````

## 2. Commit it

After saving `README.md`:

```bash
git add README.md
git commit -m "docs: update README for hackathon release"
git push

