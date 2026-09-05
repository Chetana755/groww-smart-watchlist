from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.instrument import Instrument
from app.models.watchlist import Watchlist, WatchlistItem


class WatchlistRepository:
    def list_for_user(self, session: Session, user_id: UUID) -> list[Watchlist]:
        statement = (
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .options(joinedload(Watchlist.items))
            .order_by(Watchlist.created_at, Watchlist.name)
        )
        return list(session.scalars(statement).unique())

    def get_for_user(self, session: Session, watchlist_id: UUID, user_id: UUID) -> Watchlist | None:
        statement = (
            select(Watchlist)
            .where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
            .options(joinedload(Watchlist.items).joinedload(WatchlistItem.instrument))
        )
        return session.scalar(statement)

    def add(self, session: Session, watchlist: Watchlist) -> Watchlist:
        session.add(watchlist)
        return watchlist

    def delete(self, session: Session, watchlist: Watchlist) -> None:
        session.delete(watchlist)

    def next_position(self, session: Session, watchlist_id: UUID) -> int:
        max_position = session.scalar(
            select(func.max(WatchlistItem.position)).where(
                WatchlistItem.watchlist_id == watchlist_id
            )
        )
        return (max_position or 0) + 1

    def get_item_by_symbol(
        self, session: Session, watchlist_id: UUID, symbol: str
    ) -> WatchlistItem | None:
        statement = (
            select(WatchlistItem)
            .join(WatchlistItem.instrument)
            .where(WatchlistItem.watchlist_id == watchlist_id, Instrument.symbol == symbol.upper())
            .options(joinedload(WatchlistItem.instrument))
        )
        return session.scalar(statement)
