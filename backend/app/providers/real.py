from datetime import datetime

from app.providers.base import MarketDataProvider
from app.schemas.market_data import MarketContextInput, MarketEventInput, MarketSnapshotInput


class RealMarketDataProvider(MarketDataProvider):
    """Future adapter boundary; no external provider is enabled in this phase."""

    async def get_quotes(self, symbols: list[str]) -> list[MarketSnapshotInput]:
        raise NotImplementedError("A real market-data provider is not configured.")

    async def get_context(self, symbols: list[str]) -> list[MarketContextInput]:
        raise NotImplementedError("A real market-data provider is not configured.")

    async def get_events(
        self, symbols: list[str], since: datetime | None = None
    ) -> list[MarketEventInput]:
        raise NotImplementedError("A real market-data provider is not configured.")
