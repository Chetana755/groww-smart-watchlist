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
| `POST /demo/scenario` | `{ scenarioId }` | Active scenario descriptor. |

The demo endpoint is enabled only in development/demo mode. Valid ids are `normal`, `company_move`, `sector_move`, `volume_anomaly`, `conflicting`, `stale`, and `provider_failure`.

## Semantics needed by the frontend

- `200`: complete valid response; may contain per-symbol freshness warnings.
- `206`: partial provider result; render available data and a persistent data-health notice.
- `409`: invalid state transition, including duplicate symbol/reorder mismatch.
- `422`: request validation failed.
- `503`: no usable provider result; do not clear displayed last successful overview.

`POST /refresh` returns a `comparisonSucceeded` boolean. The frontend must only describe results as “since you last checked” when true. Provider failure must not be represented as an unchanged market.
