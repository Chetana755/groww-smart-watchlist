# API Contract

Base path: `/api/v1`. JSON uses camelCase. Timestamps are ISO-8601 UTC strings. All error payloads use the shared envelope `{ "error": { "code": string, "message": string, "details"?: object } }`.

Authentication remains deliberately minimal for the hackathon. API resources are scoped through a replaceable current-user dependency (initially a seeded demo user), allowing proper authentication later without changing contracts.

## Shared response shapes

```ts
type FreshnessStatus = "fresh" | "delayed" | "stale" | "partial" | "unavailable" | "conflicting";
type Significance = "none" | "low" | "moderate" | "high";

interface Evidence {
  priceChangePct?: number;
  sectorChangePct?: number;
  indexChangePct?: number;
  relativeChangePct?: number;
  volumeRatio?: number;
  events: EventSummary[];
  scoreContributions: { signal: string; points: number; rationale: string }[];
  freshness: { status: FreshnessStatus; observedAt?: string; source?: string };
}

interface AttentionResult {
  symbol: string;
  score: number;
  significance: Significance;
  detectedReasons: string[];
  evidence: Evidence;
  thesisImpact?: { classification: "strengthened" | "weakened" | "mixed" | "unchanged"; rationale: string };
}
```

## Watchlists

| Method and path | Request | Success response |
|---|---|---|
| `GET /watchlists` | — | `WatchlistSummary[]` |
| `POST /watchlists` | `{ name: string }` | `201 Watchlist` |
| `PATCH /watchlists/{watchlistId}` | `{ name?: string, sortOrder?: number }` | `Watchlist` |
| `DELETE /watchlists/{watchlistId}` | — | `204` |
| `GET /watchlists/{watchlistId}/overview` | — | `WatchlistOverview` |
| `POST /watchlists/{watchlistId}/refresh` | `{}` | `RefreshResult` |
| `POST /watchlists/{watchlistId}/mark-seen` | `{ symbols?: string[] }` | `LastSeenResult` |

`WatchlistOverview` contains watchlist metadata, `needsAttention`, `changed`, `unchanged`, `dataHealth`, and `generatedAt`. Each stock item includes current quote values, its `AttentionResult`, and optional related-watchlist symbols.

## Implemented Phase 1 contracts

`GET /watchlists` returns `WatchlistSummary[]`; a summary has `id`, `name`, `createdAt`, `updatedAt`, and `itemCount`. `POST /watchlists` accepts `{ "name": string }` and returns a full `Watchlist` with an empty `items` list. `GET`/`PATCH`/`DELETE /watchlists/{watchlistId}` read, rename, or delete only the current user's resource. Delete returns `204`.

`POST /watchlists/{watchlistId}/items` accepts `{ "symbol": string }` and returns the new ordered item. `GET /watchlists/{watchlistId}/items` returns the ordered item list. `DELETE /watchlists/{watchlistId}/items/{symbol}` returns `204`. `PUT /watchlists/{watchlistId}/items/reorder` accepts `{ "symbols": string[] }`; the symbols must be an exact, duplicate-free permutation of the existing items and positions are reassigned from 1.

An item contains `id`, `position`, `createdAt`, and an `instrument`; an instrument has `id`, `symbol`, `companyName`, `exchange`, `sector`, and `industry`. `GET /instruments?query=` searches the catalog by symbol or company name and returns at most 20 alphabetically ordered records.

Error behavior: missing or inaccessible watchlists/instruments return `404` without exposing ownership; duplicate watchlist items return `409` with `error.code = "conflict"`; invalid reorders return `422` with `error.code = "invalid_reorder"`; malformed request data returns the shared `validation_error` envelope.

## Implemented Phase 3 contracts

`POST /market/mark-checked` records the current user's market-check time and returns `{ "lastSeenAt": "<ISO-8601 UTC timestamp>" }`. `GET /market/last-seen` returns that persisted state using the same response shape; `lastSeenAt` is `null` until the user has marked the market as checked.

## Implemented Phase 4 contracts

`GET /demo/scenarios` returns the deterministic scenario catalog, and `POST /demo/scenario` accepts `{ "scenario": "COMPANY_MOVE" }` to select the process-local scenario for the current demo user. Market quote, context, event, and attention endpoints then use that selected provider state.

`GET /market/attention` retains its score, level, reason, and evidence fields and now includes `isNew` and `latestRelevantAt`. `isNew` is true only for high/moderate attention whose latest provider observation or relevant event timestamp is later than `lastSeenAt`; when `lastSeenAt` is null, current meaningful changes are new. Stale and conflicting provider timestamps/statuses are returned unchanged.

## Watchlist stocks

| Method and path | Request | Success response |
|---|---|---|
| `POST /watchlists/{watchlistId}/stocks` | `{ symbol, watchReason?, thesisText?, reasonTags? }` | `201 WatchlistStock` |
| `PATCH /watchlists/{watchlistId}/stocks/{symbol}` | `{ watchReason?, thesisText?, reasonTags?, sortOrder? }` | `WatchlistStock` |
| `DELETE /watchlists/{watchlistId}/stocks/{symbol}` | — | `204` |
| `PATCH /watchlists/{watchlistId}/stocks/reorder` | `{ symbols: string[] }` | `WatchlistStock[]` |
| `GET /symbols/search?q={query}` | — | `SymbolSearchResult[]` |

## Stock detail and timeline

| Method and path | Success response |
|---|---|
| `GET /stocks/{symbol}` | Latest normalized quote, market/sector context, recent relevant events, freshness. |
| `GET /stocks/{symbol}/timeline?watchlistId={id}` | `TimelineEntry[]`, each carrying stored evidence and thesis impact. |
| `GET /market/context?symbol={symbol}` | Current sector/index benchmark comparison and freshness. |

## Demo controls

| Method and path | Request | Success response |
|---|---|---|
| `GET /demo/scenarios` | — | Available scenario ids, names, and descriptions. |
| `POST /demo/scenario` | `{ scenario: DemoScenario }` | Active scenario descriptor. |

Valid scenario values are `NORMAL_DAY`, `COMPANY_MOVE`, `SECTOR_MOVE`, `UNUSUAL_VOLUME`, `MIXED_SIGNALS`, `STALE_DATA`, `CONFLICTING_DATA`, and `NEW_UPDATE`. `NEW_UPDATE` supplies a fixed follow-up TCS observation at `2030-01-02T10:00:00Z`, allowing deterministic last-seen demonstrations after the baseline observation.

## Semantics needed by the frontend

- `200`: complete valid response; may contain per-symbol freshness warnings.
- `206`: partial provider result; render available data and a persistent data-health notice.
- `409`: invalid state transition, including duplicate symbol/reorder mismatch.
- `422`: request validation failed.
- `503`: no usable provider result; do not clear displayed last successful overview.

`POST /refresh` returns a `comparisonSucceeded` boolean. The frontend must only describe results as “since you last checked” when true. Provider failure must not be represented as an unchanged market.
