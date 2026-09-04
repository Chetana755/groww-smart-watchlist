# Contribution Guide

## Scope discipline

Implement only the approved phase. The product is a watchlist, not a trading, prediction, portfolio, or recommendation system.

## Backend

- Keep domain rules pure and typed; I/O belongs in providers, repositories, and services.
- Use Pydantic schemas at API boundaries and do not return ORM objects directly.
- Keep provider-specific types out of the domain layer.
- Deterministic evidence and explanations are required. AI, if added later, may only paraphrase validated evidence.
- Include source, timestamps, and status on external facts. Deduplicate cross-source descriptions of the same underlying event before producing meaningful-event output.
- Authentication is intentionally minimal during the hackathon. Keep user ownership behind a replaceable dependency; do not introduce a complex auth system without explicit approval.

## Frontend

- Use typed API clients; do not duplicate backend attention logic in the UI.
- Render data freshness and failure states honestly.
- Never use buy/sell/recommendation language.

## Quality gates

Run relevant tests, linting, formatting, type checks, and build checks before declaring a phase complete. Keep secrets in `.env`, never in committed files.
