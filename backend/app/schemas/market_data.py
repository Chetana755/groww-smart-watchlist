from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DataStatus(StrEnum):
    FRESH = "fresh"
    DELAYED = "delayed"
    STALE = "stale"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


class DemoScenario(StrEnum):
    NORMAL_DAY = "NORMAL_DAY"
    COMPANY_MOVE = "COMPANY_MOVE"
    SECTOR_MOVE = "SECTOR_MOVE"
    UNUSUAL_VOLUME = "UNUSUAL_VOLUME"
    MIXED_SIGNALS = "MIXED_SIGNALS"
    STALE_DATA = "STALE_DATA"
    CONFLICTING_DATA = "CONFLICTING_DATA"
    NEW_UPDATE = "NEW_UPDATE"


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MarketSnapshotInput(ApiModel):
    symbol: str
    price: float
    previous_close: float
    absolute_change: float
    percentage_change: float
    volume: int
    average_volume: int
    timestamp: datetime
    data_status: DataStatus
    source: str
    day_high: float | None = None
    day_low: float | None = None
    open: float | None = None


class MarketContextInput(ApiModel):
    symbol: str
    sector: str
    sector_change_pct: float
    index_name: str
    index_change_pct: float
    comparison_symbols: list[str] = Field(default_factory=list)
    timestamp: datetime
    data_status: DataStatus
    source: str


class MarketEventInput(ApiModel):
    event_id: str
    symbol: str
    event_type: str
    title: str
    occurred_at: datetime
    source: str
    source_event_id: str | None = None
    relevance_metadata: dict[str, str] = Field(default_factory=dict)
    data_status: DataStatus = DataStatus.FRESH

    @property
    def dedupe_key(self) -> str:
        identity = (self.source_event_id or self.title).strip().lower().replace(" ", "-")
        return f"{self.symbol}:{self.event_type}:{identity}:{self.occurred_at.date().isoformat()}"


class CanonicalMarketEvent(ApiModel):
    event_id: str
    symbol: str
    event_type: str
    title: str
    occurred_at: datetime
    source: str
    source_event_id: str | None = None
    relevance_metadata: dict[str, str] = Field(default_factory=dict)
    data_status: DataStatus
    dedupe_key: str
    corroborating_sources: list[str] = Field(default_factory=list)


class DemoScenarioResponse(ApiModel):
    scenario: DemoScenario
    title: str
    description: str
    source: str = "Deterministic Demo Provider"


class DemoScenarioSelectionRequest(ApiModel):
    scenario: DemoScenario


class LastSeenResponse(ApiModel):
    last_seen_at: datetime | None
