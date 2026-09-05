from datetime import UTC, datetime

from app.providers.base import MarketDataProvider
from app.schemas.market_data import (
    DataStatus,
    DemoScenario,
    DemoScenarioResponse,
    MarketContextInput,
    MarketEventInput,
    MarketSnapshotInput,
)

SOURCE = "Deterministic Demo Exchange Feed"
OBSERVED_AT = datetime(2026, 9, 4, 10, 0, tzinfo=UTC)
STALE_AT = datetime(2026, 8, 29, 10, 0, tzinfo=UTC)
NEW_UPDATE_AT = datetime(2030, 1, 2, 10, 0, tzinfo=UTC)
NEW_UPDATE_EVENT_AT = datetime(2030, 1, 2, 9, 15, tzinfo=UTC)

INSTRUMENTS = {
    "RELIANCE": (1450.0, "Energy"),
    "TCS": (3200.0, "Information Technology"),
    "INFY": (1500.0, "Information Technology"),
    "HDFCBANK": (1750.0, "Financial Services"),
    "ICICIBANK": (1350.0, "Financial Services"),
    "SBIN": (800.0, "Financial Services"),
    "ITC": (450.0, "Consumer Defensive"),
    "LT": (3600.0, "Industrials"),
    "WIPRO": (550.0, "Information Technology"),
    "HCLTECH": (1600.0, "Information Technology"),
}

SCENARIOS = {
    DemoScenario.NORMAL_DAY: ("Normal day", "Ordinary market moves and normal volumes."),
    DemoScenario.COMPANY_MOVE: ("Company move", "TCS moves independently on elevated volume."),
    DemoScenario.SECTOR_MOVE: ("Sector move", "Information-technology shares rise together."),
    DemoScenario.UNUSUAL_VOLUME: (
        "Unusual volume",
        "A modest move arrives with highly abnormal volume.",
    ),
    DemoScenario.MIXED_SIGNALS: (
        "Mixed signals",
        "Strong move, abnormal volume, and contextual event evidence.",
    ),
    DemoScenario.STALE_DATA: (
        "Stale data",
        "Snapshots carry intentionally old timestamps and stale status.",
    ),
    DemoScenario.CONFLICTING_DATA: (
        "Conflicting data",
        "Multiple source observations disagree and remain visible.",
    ),
    DemoScenario.NEW_UPDATE: (
        "New update",
        "A later deterministic TCS follow-up update for last-seen demonstrations.",
    ),
}


class DeterministicDemoMarketDataProvider(MarketDataProvider):
    def __init__(self, scenario: DemoScenario = DemoScenario.NORMAL_DAY) -> None:
        self.scenario = scenario

    async def get_quotes(self, symbols: list[str]) -> list[MarketSnapshotInput]:
        normalized = [symbol.upper() for symbol in symbols if symbol.upper() in INSTRUMENTS]
        quotes = [self._quote(symbol) for symbol in normalized]
        if self.scenario == DemoScenario.CONFLICTING_DATA and "TCS" in normalized:
            quotes.append(
                self._quote(
                    "TCS",
                    source="Deterministic Demo Alt Feed",
                    pct=3.6,
                    status=DataStatus.CONFLICTING,
                )
            )
        return quotes

    async def get_context(self, symbols: list[str]) -> list[MarketContextInput]:
        return [
            self._context(symbol.upper()) for symbol in symbols if symbol.upper() in INSTRUMENTS
        ]

    async def get_events(
        self, symbols: list[str], since: datetime | None = None
    ) -> list[MarketEventInput]:
        events = [
            event
            for event in self._events()
            if event.symbol in {symbol.upper() for symbol in symbols}
        ]
        return [event for event in events if since is None or event.occurred_at > since]

    def _quote(
        self,
        symbol: str,
        source: str = SOURCE,
        pct: float | None = None,
        status: DataStatus | None = None,
    ) -> MarketSnapshotInput:
        base_price, _ = INSTRUMENTS[symbol]
        scenario_pct, volume_ratio = self._signal(symbol)
        percentage_change = scenario_pct if pct is None else pct
        average_volume = 1_000_000
        price = round(base_price * (1 + percentage_change / 100), 2)
        previous_close = base_price
        return MarketSnapshotInput(
            symbol=symbol,
            price=price,
            previous_close=previous_close,
            absolute_change=round(price - previous_close, 2),
            percentage_change=percentage_change,
            volume=round(average_volume * volume_ratio),
            average_volume=average_volume,
            timestamp=self._observation_timestamp(),
            data_status=status
            or (DataStatus.STALE if self.scenario == DemoScenario.STALE_DATA else DataStatus.FRESH),
            source=source,
            day_high=round(price * 1.012, 2),
            day_low=round(price * 0.988, 2),
            open=round(previous_close * (1 + percentage_change / 200), 2),
        )

    def _signal(self, symbol: str) -> tuple[float, float]:
        if self.scenario == DemoScenario.COMPANY_MOVE and symbol == "TCS":
            return 4.2, 2.4
        if self.scenario == DemoScenario.SECTOR_MOVE and symbol in {
            "TCS",
            "INFY",
            "WIPRO",
            "HCLTECH",
        }:
            return {"TCS": 2.8, "INFY": 2.5, "WIPRO": 2.6, "HCLTECH": 2.7}[symbol], 1.4
        if self.scenario == DemoScenario.UNUSUAL_VOLUME and symbol == "INFY":
            return 0.8, 3.1
        if self.scenario == DemoScenario.MIXED_SIGNALS and symbol == "RELIANCE":
            return -3.4, 2.2
        if self.scenario == DemoScenario.CONFLICTING_DATA and symbol == "TCS":
            return 4.2, 2.4
        if self.scenario == DemoScenario.NEW_UPDATE and symbol == "TCS":
            return 5.5, 3.2
        return 0.35, 1.05

    def _context(self, symbol: str) -> MarketContextInput:
        _, sector = INSTRUMENTS[symbol]
        sector_change = 0.4
        if self.scenario == DemoScenario.COMPANY_MOVE and sector == "Information Technology":
            sector_change = 0.5
        elif self.scenario == DemoScenario.SECTOR_MOVE and sector == "Information Technology":
            sector_change = 2.6
        elif self.scenario == DemoScenario.MIXED_SIGNALS and symbol == "RELIANCE":
            sector_change = -1.0
        comparisons = [
            candidate
            for candidate, (_, candidate_sector) in INSTRUMENTS.items()
            if candidate_sector == sector and candidate != symbol
        ]
        return MarketContextInput(
            symbol=symbol,
            sector=sector,
            sector_change_pct=sector_change,
            index_name="NIFTY 50",
            index_change_pct=0.3,
            comparison_symbols=comparisons,
            timestamp=self._observation_timestamp(),
            data_status=DataStatus.STALE
            if self.scenario == DemoScenario.STALE_DATA
            else DataStatus.FRESH,
            source=SOURCE,
        )

    def _events(self) -> list[MarketEventInput]:
        if self.scenario == DemoScenario.COMPANY_MOVE:
            return [
                self._event("TCS", "earnings", "TCS reports quarterly results", "tcs-q1-results")
            ]
        if self.scenario == DemoScenario.MIXED_SIGNALS:
            return [
                self._event(
                    "RELIANCE",
                    "corporate_announcement",
                    "Refinery maintenance announced",
                    "reliance-maintenance",
                )
            ]
        if self.scenario == DemoScenario.CONFLICTING_DATA:
            primary = self._event(
                "TCS", "earnings", "TCS reports quarterly results", "tcs-q1-results"
            )
            duplicate = primary.model_copy(
                update={"event_id": "alt-tcs-q1", "source": "Deterministic Demo Newswire"}
            )
            return [primary, duplicate]
        if self.scenario == DemoScenario.NEW_UPDATE:
            return [
                self._event(
                    "TCS",
                    "company_announcement",
                    "TCS follow-up business update released",
                    "tcs-follow-up-update",
                    occurred_at=NEW_UPDATE_EVENT_AT,
                )
            ]
        return []

    @staticmethod
    def _event(
        symbol: str,
        event_type: str,
        title: str,
        source_event_id: str,
        occurred_at: datetime = datetime(2026, 9, 4, 9, 15, tzinfo=UTC),
    ) -> MarketEventInput:
        return MarketEventInput(
            event_id=f"demo-{source_event_id}",
            symbol=symbol,
            event_type=event_type,
            title=title,
            occurred_at=occurred_at,
            source=SOURCE,
            source_event_id=source_event_id,
            relevance_metadata={"scenario": "demo"},
        )

    def _observation_timestamp(self) -> datetime:
        if self.scenario == DemoScenario.STALE_DATA:
            return STALE_AT
        if self.scenario == DemoScenario.NEW_UPDATE:
            return NEW_UPDATE_AT
        return OBSERVED_AT


def scenario_catalog() -> list[DemoScenarioResponse]:
    return [
        DemoScenarioResponse(scenario=scenario, title=title, description=description)
        for scenario, (title, description) in SCENARIOS.items()
    ]
