# Data Model

## Conventions

All tables use UUID primary keys, timezone-aware UTC timestamps, and `created_at`/`updated_at` where mutable. Snapshots and change events are append-only after creation. JSONB fields contain versioned structured data, not unvalidated provider payloads.

## Entities

| Entity | Essential fields | Relationships and constraints |
|---|---|---|
| `users` | `id`, `display_name`, `email` nullable, `last_market_check_at` nullable | Owns watchlists. `last_market_check_at` records the user's most recent successful market check. A seeded demo user is acceptable before authentication. |
| `watchlists` | `id`, `user_id`, `name`, `sort_order` | Belongs to one user; unique `(user_id, name)`. |
| `watchlist_stocks` | `id`, `watchlist_id`, `symbol`, `sort_order`, `watch_reason`, `thesis_text`, `reason_tags` | Belongs to one watchlist; unique `(watchlist_id, symbol)`. |
| `market_snapshots` | `id`, `symbol`, `price`, `previous_close`, `volume`, `normal_volume`, `sector`, `provider`, `observed_at`, `status`, `raw_metadata` | Immutable normalized observation; index `(symbol, observed_at DESC)`. |
| `market_context_snapshots` | `id`, `benchmark_kind`, `benchmark_key`, `return_pct`, `provider`, `observed_at`, `status` | Sector/index observations; unique benchmark-time/provider combination. |
| `market_events` | `id`, `event_type`, `title`, `summary`, `source`, `source_event_id`, `dedupe_key`, `occurred_at`, `received_at`, `confidence`, `status` | Linked to zero or more symbols through `market_event_symbols`; unique source event id when present and indexed `dedupe_key` for cross-source underlying-event deduplication. |
| `market_event_symbols` | `event_id`, `symbol` | Many-to-many event/symbol mapping. |
| `last_seen_states` | `id`, `user_id`, `watchlist_id`, `symbol`, `snapshot_id`, `seen_at` | One row per `(user_id, watchlist_id, symbol)`; references the baseline snapshot. |
| `change_events` | `id`, `watchlist_stock_id`, `snapshot_id`, `baseline_snapshot_id`, `score`, `significance`, `detected_reasons`, `evidence`, `reliability_status`, `generated_at` | Timeline and audit record for a refresh; index `(watchlist_stock_id, generated_at DESC)`. |
| `thesis_impacts` | `id`, `change_event_id`, `classification`, `rationale`, `evidence` | One-to-one with a change event when a watch reason/thesis exists. |
| `stock_relationships` | `id`, `source_symbol`, `related_symbol`, `relationship_type`, `confidence`, `source` | Unique `(source_symbol, related_symbol, relationship_type)`; relationships are modest and curated. |

## Relationship graph

```text
User 1--* Watchlist 1--* WatchlistStock
                         |       |
                         |       *--* ChangeEvent *--1 MarketSnapshot
                         |                    |
                         |                    0..1 ThesisImpact
                         |
User + Watchlist + Symbol 1--1 LastSeenState *--1 MarketSnapshot

MarketEvent *--* Symbol (market_event_symbols)
StockRelationship: Symbol -- relationship --> Symbol
```

## Required enums

- `significance`: `none`, `low`, `moderate`, `high`
- `freshness/status`: `fresh`, `delayed`, `stale`, `partial`, `unavailable`, `conflicting`
- `event_type`: `earnings`, `company_announcement`, `corporate_action`, `major_news`, `other`
- `thesis classification`: `strengthened`, `weakened`, `mixed`, `unchanged`
- `relationship_type`: `same_sector`, `same_industry`, `competitor`, `supplier_customer`

## Persistence rules

1. Store a snapshot/event before any result that cites it.
2. A change event cites both its current and baseline snapshot, where a baseline exists.
3. New watchlist stocks have no baseline: display current data and establish a baseline after a successful refresh, without claiming historical change.
4. Advance `last_seen_states` only in the successful refresh transaction after all comparison output has been recorded.
5. Provider errors and missing records are persisted as status/metadata only when a valid normalized record exists; missing numerical values remain absent, never zero-filled.
6. Event ingestion creates a normalized cross-source `dedupe_key` from source identifiers when available; otherwise it uses normalized event type, affected symbols, occurrence-time window, and a content fingerprint. Multiple reports matching one key enrich corroboration/source provenance but produce one canonical market event and one meaningful-event contribution.

## Implemented Phase 1 invariants

- `watchlists.user_id` is a foreign key to `users`; all API access scopes a lookup by both identifiers.
- `watchlist_items.watchlist_id` and `watchlist_items.instrument_id` are foreign keys with a database-level unique constraint `uq_watchlist_item_instrument`. A symbol cannot occur twice in one watchlist even under concurrent requests.
- Item `position` is explicit, one-based, and assigned at the end of the list on insertion. Reorder accepts only a full permutation of existing symbols, then updates all positions in one committed transaction.
- The `instruments` table is seeded through migration `20260904_01` with the deterministic Indian-equity demo catalog. API handlers access it through `InstrumentRepository`, not hard-coded values.
