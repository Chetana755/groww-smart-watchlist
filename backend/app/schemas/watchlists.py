from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.instruments import InstrumentResponse


class WatchlistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WatchlistUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WatchlistItemCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    position: int
    created_at: datetime
    instrument: InstrumentResponse


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    items: list[WatchlistItemResponse] = Field(default_factory=list)


class WatchlistSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    item_count: int


class ReorderWatchlistItemsRequest(BaseModel):
    symbols: list[str] = Field(max_length=100)
