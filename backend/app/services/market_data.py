from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.attention import calculate_attention
from app.domain.errors import NotFoundError
from app.models.user import User
from app.providers.base import MarketDataProvider
from app.providers.demo import DeterministicDemoMarketDataProvider, scenario_catalog
from app.repositories.users import UserRepository
from app.schemas.attention import (
    AttentionEvidenceResponse,
    AttentionResponse,
)
from app.schemas.market_data import (
    CanonicalMarketEvent,
    DemoScenario,
    DemoScenarioResponse,
    MarketContextInput,
    MarketEventInput,
    MarketSnapshotInput,
)


class DemoScenarioStore:
    """Process-local demo preference; snapshots remain provider data, not persisted records."""

    def __init__(self) -> None:
        self._scenarios: dict[UUID, DemoScenario] = {}

    def get(self, user_id: UUID) -> DemoScenario:
        return self._scenarios.get(user_id, DemoScenario.NORMAL_DAY)

    def set(self, user_id: UUID, scenario: DemoScenario) -> None:
        self._scenarios[user_id] = scenario


class MarketDataService:
    def __init__(self, scenario_store: DemoScenarioStore | None = None) -> None:
        self.scenario_store = scenario_store or DemoScenarioStore()
        self.users = UserRepository()

    def mark_market_checked(self, session: Session, user_id: UUID) -> datetime:
        user = self._user(session, user_id)
        checked_at = datetime.now(UTC)
        user.last_market_check_at = checked_at
        session.commit()
        return checked_at

    def last_market_check_at(self, session: Session, user_id: UUID) -> datetime | None:
        checked_at = self._user(session, user_id).last_market_check_at
        if checked_at is not None and checked_at.tzinfo is None:
            return checked_at.replace(tzinfo=UTC)
        return checked_at

    def provider_for(self, user_id: UUID) -> MarketDataProvider:
        return DeterministicDemoMarketDataProvider(self.scenario_store.get(user_id))

    async def quotes(self, user_id: UUID, symbols: list[str]) -> list[MarketSnapshotInput]:
        return await self.provider_for(user_id).get_quotes(self._symbols(symbols))

    async def context(self, user_id: UUID, symbols: list[str]) -> list[MarketContextInput]:
        return await self.provider_for(user_id).get_context(self._symbols(symbols))

    async def events(
        self, user_id: UUID, symbols: list[str], since: datetime | None = None
    ) -> list[CanonicalMarketEvent]:
        raw_events = await self.provider_for(user_id).get_events(self._symbols(symbols), since)
        return self.deduplicate_events(raw_events)

    async def attention(
        self, session: Session, user_id: UUID, symbols: list[str]
    ) -> list[AttentionResponse]:
        quotes = await self.quotes(user_id, symbols)
        contexts = await self.context(user_id, symbols)
        events = await self.events(user_id, symbols)

        context_by_symbol = {item.symbol: item for item in contexts}
        events_by_symbol: dict[str, list[CanonicalMarketEvent]] = {}
        for event in events:
            events_by_symbol.setdefault(event.symbol, []).append(event)
        last_seen_at = self.last_market_check_at(session, user_id)

        results = []

        for quote in quotes:
            context = context_by_symbol.get(quote.symbol)

            if context is None:
                continue

            symbol_events = events_by_symbol.get(quote.symbol, [])
            latest_relevant_at = max(
                [quote.timestamp, *(event.occurred_at for event in symbol_events)]
            )

            result = calculate_attention(
                price_change_pct=quote.percentage_change,
                volume=quote.volume,
                average_volume=quote.average_volume,
                sector_change_pct=context.sector_change_pct,
                index_change_pct=context.index_change_pct,
                has_relevant_event=bool(symbol_events),
            )

            results.append(
                AttentionResponse(
                    symbol=quote.symbol,
                    score=result.score,
                    level=result.level,
                    is_new=(
                        result.level.value in {"high", "moderate"}
                        and (last_seen_at is None or latest_relevant_at > last_seen_at)
                    ),
                    latest_relevant_at=latest_relevant_at,
                    reasons=list(result.reasons),
                    evidence=AttentionEvidenceResponse(
                        priceScore=result.evidence.price_score,
                        volumeScore=result.evidence.volume_score,
                        relativeScore=result.evidence.relative_score,
                        volatilityScore=result.evidence.volatility_score,
                        eventScore=result.evidence.event_score,
                        relevanceScore=result.evidence.relevance_score,
                    ),
                )
            )

        return results

    def scenarios(self) -> list[DemoScenarioResponse]:
        return scenario_catalog()

    def select_scenario(self, user_id: UUID, scenario: DemoScenario) -> DemoScenarioResponse:
        self.scenario_store.set(user_id, scenario)
        return next(item for item in self.scenarios() if item.scenario == scenario)

    def _user(self, session: Session, user_id: UUID) -> User:
        user = self.users.get_by_id(session, user_id)
        if user is None:
            raise NotFoundError("User was not found.")
        return user

    @staticmethod
    def deduplicate_events(events: list[MarketEventInput]) -> list[CanonicalMarketEvent]:
        groups: dict[str, list[MarketEventInput]] = {}
        for event in events:
            groups.setdefault(event.dedupe_key, []).append(event)
        canonical_events = []
        for dedupe_key, duplicates in groups.items():
            canonical = sorted(
                duplicates, key=lambda event: (event.occurred_at, event.source, event.event_id)
            )[0]
            corroborating_sources = sorted(
                {event.source for event in duplicates if event.source != canonical.source}
            )
            canonical_events.append(
                CanonicalMarketEvent(
                    **canonical.model_dump(),
                    dedupe_key=dedupe_key,
                    corroborating_sources=corroborating_sources,
                )
            )
        return sorted(
            canonical_events, key=lambda event: (event.occurred_at, event.event_id), reverse=True
        )

    @staticmethod
    def _symbols(symbols: list[str]) -> list[str]:
        return list(dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip()))


market_data_service = MarketDataService()
