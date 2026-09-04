# Smart Market Watchlist Architecture

## Purpose and boundaries

The product is a smart watchlist: it helps a user understand what changed in watched securities, why it changed, and whether the change is relevant to the user's stated watch reason. It does not predict prices, recommend trades, execute trades, manage portfolios, or provide robo-advice.

## System shape

```text
React + TypeScript + Vite
        | typed JSON/HTTP API
FastAPI modular monolith
  api -> services -> domain <- providers
          |            |
       repositories  deterministic attention engine
          |
      PostgreSQL
```

The frontend owns presentation and client state. The backend owns validation, persistence, market-data normalization, last-seen comparison, deterministic scoring, and evidence generation. Business rules live in pure `domain` functions and must not depend on FastAPI, SQLAlchemy, or a market-data vendor.

## Backend module ownership

| Module | Responsibility | Must not do |
|---|---|---|
| `api` | Request validation, HTTP status codes, response DTOs | Implement scoring or query providers directly |
| `services` | Orchestrate use cases and transactions | Contain vendor-specific payload logic |
| `domain` | Scoring, significance, evidence, thesis classification | Perform I/O |
| `providers` | Fetch/validate/normalize market and event data | Decide user attention |
| `repositories` | SQLAlchemy reads and writes | Apply product policy |
| `models` | Database mappings | Leak ORM entities to API clients |
| `schemas` | Pydantic API/provider contracts | Persist data |

## Data and refresh flow

1. The dashboard requests `POST /watchlists/{id}/refresh` or loads its saved overview.
2. `RefreshWatchlistService` reads stocks and their last-seen baselines.
3. A `MarketDataProvider` returns normalized quotes, contexts, and events.
4. The service validates completeness/freshness, persists immutable snapshots/events, and calls the pure attention engine.
5. It stores change events and thesis impacts in one transaction.
6. The response is returned; only after successful comparison/persistence are last-seen states advanced.

If a provider fails or necessary data is unavailable, return an explicit partial/error status and preserve the existing baseline. Never fabricate a market value or event.

## Provider boundary

```python
class MarketDataProvider(Protocol):
    async def get_quotes(self, symbols: list[str]) -> list[MarketSnapshotInput]: ...
    async def get_context(self, symbols: list[str]) -> list[MarketContextInput]: ...
    async def get_events(self, symbols: list[str], since: datetime | None) -> list[MarketEventInput]: ...
```

`DeterministicDemoMarketDataProvider` is the default development/demo implementation and owns seven reproducible scenarios. `RealMarketDataProvider` is an adapter only; its raw response never crosses into services or the domain layer.

## Explanation boundary

The deterministic evidence and template-based explanation layer is core product intelligence and must always work without AI. It emits structured evidence and concise fact-based explanations. A future optional `ExplanationProvider` may enhance wording from that validated evidence, but it cannot select significance, calculate a score, introduce market facts, or make recommendations. Absence or failure of AI must never reduce core functionality.

## Authentication boundary

Hackathon authentication is intentionally minimal: development uses a seeded/demo user resolved through a replaceable current-user dependency. Routes and ownership checks accept this dependency rather than directly assuming a user. A later identity provider can replace the dependency without changing domain logic, repositories, or API resource ownership. No complex login, password, or session system is in Phase 0.

## Reliability model

Each external fact includes `source`, `observed_at` (or `occurred_at`), `received_at` where applicable, and a freshness/status value. Valid statuses are `fresh`, `delayed`, `stale`, `partial`, `unavailable`, and `conflicting`. Reliability warnings are visible in overview and detail responses and can reduce attention score according to domain rules. Before an event contributes to attention, provider normalization must deduplicate reports of the same underlying event across sources using stable external IDs where available, otherwise normalized affected symbols, event type, occurrence-time window, and content fingerprint. A duplicate report may improve source corroboration but must not create a second meaningful event.

## Deployment shape

Docker Compose runs `frontend`, `backend`, and `postgres`. Environment configuration is provided through `.env` (never committed); `.env.example` documents non-secret settings. The backend remains stateless so it can scale horizontally. Provider polling/jobs are deliberately deferred until required; the initial refresh is request-driven.
