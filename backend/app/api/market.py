from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.attention import AttentionResponse
from app.schemas.market_data import (
    CanonicalMarketEvent,
    LastSeenResponse,
    MarketContextInput,
    MarketSnapshotInput,
)
from app.services.market_data import market_data_service

router = APIRouter(prefix="/market", tags=["market-data"])
service = market_data_service


def symbols_from_query(symbols: str) -> list[str]:
    return [symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()]


@router.post("/mark-checked", response_model=LastSeenResponse)
def mark_checked(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> LastSeenResponse:
    return LastSeenResponse(last_seen_at=service.mark_market_checked(session, current_user.id))


@router.get("/last-seen", response_model=LastSeenResponse)
def get_last_seen(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> LastSeenResponse:
    return LastSeenResponse(last_seen_at=service.last_market_check_at(session, current_user.id))


@router.get("/attention", response_model=list[AttentionResponse])
async def get_attention(
    symbols: str = Query(min_length=1, max_length=500),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[AttentionResponse]:
    return await service.attention(session, current_user.id, symbols_from_query(symbols))


@router.get("/quotes", response_model=list[MarketSnapshotInput])
async def get_quotes(
    symbols: str = Query(min_length=1, max_length=500),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[MarketSnapshotInput]:
    return await service.quotes(session, current_user.id, symbols_from_query(symbols))


@router.get("/context", response_model=list[MarketContextInput])
async def get_context(
    symbols: str = Query(min_length=1, max_length=500),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[MarketContextInput]:
    return await service.context(session, current_user.id, symbols_from_query(symbols))


@router.get("/events", response_model=list[CanonicalMarketEvent])
async def get_events(
    symbols: str = Query(min_length=1, max_length=500),
    since: datetime | None = None,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[CanonicalMarketEvent]:
    return await service.events(session, current_user.id, symbols_from_query(symbols), since)
