# Executable 36-Hour Engineering Roadmap

## Phase 0 — Foundations (hours 0–3)

Create: `README.md`, `AGENTS.md`, `.env.example`, `docker-compose.yml`, `backend/pyproject.toml`, Alembic configuration, `backend/app/main.py`, `backend/app/config.py`, `backend/app/api/health.py`, `backend/app/schemas/common.py`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, and CI/lint configuration. Use a replaceable seeded-demo-user dependency only; do not build full authentication.

Dependencies: none. Backend and frontend scaffolds can proceed in parallel after shared environment names and API base path are agreed.

Contracts: `GET /api/v1/health -> { status, version }`. Establish shared error envelope in backend schemas and matching frontend types.

Integration: Vite reads `VITE_API_BASE_URL`; FastAPI enables configured development CORS only.

Exit tests: backend health API test, frontend render smoke test, lint/type-check for both apps, Docker Compose startup smoke test.

## Phase 1 — Persistence and watchlist management (hours 3–7)

Create: `backend/app/db/session.py`, `backend/app/db/base.py`, `backend/alembic/`, `backend/app/models/{user,watchlist,watchlist_stock}.py`, `backend/app/repositories/{watchlists,watchlist_stocks}.py`, `backend/app/services/watchlists.py`, `backend/app/schemas/watchlists.py`, `backend/app/api/watchlists.py`, `backend/app/api/symbols.py`, `backend/app/seed/symbol_catalog.py`; frontend `features/watchlists/*`, `pages/WatchlistsPage.tsx`, and `api/watchlists.ts`.

Dependencies: Phase 0. Migrations precede repositories; schemas precede route/frontend integration. Symbol catalog/search may be built in parallel with CRUD.

Entities: `users -> watchlists -> watchlist_stocks`; enforce unique watchlist names per user and symbols per watchlist.

Contracts: all CRUD/search endpoints in `api-contract.md`, including `409` for duplicate symbols and invalid reorder lists.

Integration: frontend renders server-created ids and performs optimistic UI only after a typed rollback strategy exists; otherwise invalidate/refetch.

Exit tests: migration-up test; repository tests for ownership, duplicate prevention and reorder; API CRUD/validation tests; frontend tests for add/remove/rename/reorder behavior.

Implementation note: Phase 1 is complete with migration `20260904_01`. It includes the deterministic demo-user resolver as a replaceable API dependency, the normalized instrument catalog, CRUD/item APIs, and the focused watchlist-management interface only. No market-intelligence Phase 2+ functionality is included.

## Phase 2 — Market-data contracts and deterministic scenarios (hours 7–11)

Create: `backend/app/providers/base.py`, `backend/app/providers/demo.py`, `backend/app/providers/real.py`, `backend/app/providers/fixtures/*.json`, `backend/app/schemas/market_data.py`, `backend/app/models/{market_snapshot,market_context_snapshot,market_event}.py`, `backend/app/repositories/market_data.py`, `backend/app/services/demo.py`, `backend/app/api/demo.py`; frontend `features/demo/ScenarioSelector.tsx`. Market-event normalization includes cross-source deduplication before event persistence and before attention scoring.

Dependencies: Phase 0 for runtime; Phase 1 only if scenarios must seed a user watchlist. Provider code can be parallelized with schema/model work once the shared normalized DTO contract is fixed.

Contracts: provider protocol in architecture document; demo endpoints and `FreshnessStatus` API type in `api-contract.md`.

Entities: immutable market snapshots/context snapshots, events, and event-symbol join rows. All normalized records include source, timestamps, and status.

Integration: selector calls `POST /demo/scenario`; every subsequent refresh reads the active server-side scenario. Frontend displays scenario label/source rather than calling providers.

Exit tests: fixture determinism test for all seven scenarios; provider contract tests; stale timestamps/status tests; provider-failure test confirming no fabricated quote; demo endpoint validation tests.

## Phase 3 — Attention, evidence, thesis, and last-seen domain (hours 11–18)

Create: `backend/app/domain/{attention,evidence,thesis,relationships}.py`, `backend/app/services/refresh_watchlist.py`, `backend/app/models/{last_seen_state,change_event,thesis_impact,stock_relationship}.py`, matching repositories/schemas, `backend/app/api/overview.py`, `backend/app/api/market.py`, `backend/app/api/timeline.py`, and seed relationship data.

Dependencies: Phase 1 watchlist membership and Phase 2 normalized provider data/models. The pure domain functions can be developed in parallel with database/repository implementation after input/output DTOs are frozen. Refresh orchestration must follow both.

Contracts: overview, refresh, market context, and timeline endpoints in `api-contract.md`. Refresh response includes `comparisonSucceeded`, data health, grouped results, and evidence.

Entities: `last_seen_states` references baseline snapshots; `change_events` references current/baseline snapshots and one optional `thesis_impact`; relationships remain symbol-level.

Integration: frontend consumes evidence directly; it does not recalculate scores. A failed/partial refresh retains the prior overview and displays backend-provided health status.

Exit tests before UI work: threshold-boundary unit tests; score contribution/evidence snapshots; sector-relative and volume rules; stale/conflict penalties; thesis classifications; new-stock/no-baseline behavior; atomic transaction test proving baseline is unchanged on failure; timeline persistence test.

## Phase 4 — Primary dashboard and attention experience (hours 18–23)

Create: `frontend/src/pages/DashboardPage.tsx`, `features/attention/{AttentionCard,AttentionList,EvidenceDrawer,DataHealthBanner}.tsx`, `features/market/{WatchlistTable,QuoteCell,FreshnessBadge}.tsx`, `api/overview.ts`, `types/api.ts`, and component tests.

Dependencies: Phase 3 API contract and its exit tests. Component shell/styling may be parallelized with Phase 3, but data binding is sequential.

Integration: call overview on selection and refresh on user action; render `needsAttention`, `changed`, and collapsed `unchanged`; map 206/503 behavior as specified in the contract.

Exit tests: typed client tests, loading/empty/error/partial-state tests, evidence rendering test, score/significance ordering test, and dashboard API mock integration test.

## Phase 5 — Detail, timeline, thesis and ripple (hours 23–27)

Create: `frontend/src/pages/StockDetailPage.tsx`, `features/timeline/Timeline.tsx`, `features/thesis/{ThesisEditor,ThesisImpactCard}.tsx`, `features/relationships/RelatedStocksPanel.tsx`, `api/stocks.ts`, and route definitions.

Dependencies: Phase 1 editing API and Phase 3 timeline/thesis/relationship APIs. Timeline panel, thesis editor, and related-stocks panel may be implemented in parallel after contracts are stable.

Integration: detail fetches `GET /stocks/{symbol}`, timeline uses selected watchlist id, thesis editor PATCHes its watchlist-stock record then refetches overview/detail.

Exit tests: timeline ordering/evidence tests, all four thesis-impact states, missing-thesis state, related-stock filtering to the active watchlist, and no-advice copy regression test.

## Phase 6 — Reliability, polish, and accessibility (hours 27–30)

Create: frontend shared `components/{EmptyState,ErrorState,LoadingState}.tsx`, `lib/formatters.ts`, CSS/theme/accessibility updates; backend logging/error mapping and health/readiness refinements.

Dependencies: Phases 4–5. Visual polish tasks can run in parallel; shared loading/error conventions should be set before final screen integration.

Integration: ensure error IDs/messages from API map to user-safe UI copy. Display source and timestamp next to all external market data.

Exit tests: keyboard navigation smoke tests, accessibility scan, stale/partial/unavailable UI snapshots, responsive dashboard/detail smoke tests.

## Phase 7 — End-to-end verification and demo packaging (hours 30–36)

Create: `backend/tests/integration/test_refresh_flow.py`, `frontend/e2e/watchlist.spec.ts`, `docs/demo-script.md`, and complete `README.md` runbook.

Dependencies: all prior phases. Test writing can begin earlier, but the final scenario matrix and production-like Compose verification are sequential.

Required end-to-end flow: create watchlist, add/reorder stocks, select every deterministic scenario, refresh, inspect evidence/timeline/thesis/ripple, simulate provider failure, verify last-seen preservation, reload and compare.

Exit tests: full test suite, database migration from clean state, Docker Compose startup, all seven deterministic scenario assertions, frontend production build, and a manual judging walkthrough.

## Parallelization summary

Safe parallel tracks after Phase 0: (A) frontend shell/types and (B) backend persistence; within Phase 2, fixtures/provider and ORM/migration; within Phase 3, pure scoring tests and persistence/orchestration; within Phase 5, timeline, thesis, and related-stocks UI.

Sequential work: normalized provider DTOs before provider implementation; migrations before repository/service integration; attention input/output contracts before refresh orchestration; refresh contract/tests before dashboard binding; all feature integration before end-to-end demo verification.

## Critical-path dependency graph

```text
Phase 0: shared scaffold + contract conventions
  -> Phase 1: watchlist persistence/API
  -> Phase 2: normalized demo provider + market persistence
  -> Phase 3: attention engine + last-seen transactional refresh
  -> Phase 4: dashboard and evidence UI
  -> Phase 5: detail/timeline/thesis/ripple UI
  -> Phase 6: reliability/accessibility polish
  -> Phase 7: full scenario E2E and demo packaging

Parallel, non-critical contributors:
Phase 0 frontend shell ---------------------------> Phase 4 binding
Phase 2 fixture authoring -------------------------> Phase 3 provider inputs
Phase 3 pure-domain test authoring ---------------> Phase 3 orchestration
Phase 5 timeline | thesis | ripple UI ------------> Phase 6
```
