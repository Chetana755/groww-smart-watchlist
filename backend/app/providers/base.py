from datetime import datetime
from typing import Protocol

from app.schemas.market_data import MarketContextInput, MarketEventInput, MarketSnapshotInput


class MarketDataProvider(Protocol):
    async def get_quotes(self, symbols: list[str]) -> list[MarketSnapshotInput]: ...

    async def get_context(self, symbols: list[str]) -> list[MarketContextInput]: ...

    async def get_events(
        self, symbols: list[str], since: datetime | None = None
    ) -> list[MarketEventInput]: ...
