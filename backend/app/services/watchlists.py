from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.errors import ConflictError, NotFoundError
from app.domain.ordering import validate_reorder
from app.models.watchlist import Watchlist, WatchlistItem
from app.repositories.instruments import InstrumentRepository
from app.repositories.watchlists import WatchlistRepository


class WatchlistService:
    def __init__(self) -> None:
        self.watchlists = WatchlistRepository()
        self.instruments = InstrumentRepository()

    def list_watchlists(self, session: Session, user_id: UUID) -> list[Watchlist]:
        return self.watchlists.list_for_user(session, user_id)

    def get_watchlist(self, session: Session, user_id: UUID, watchlist_id: UUID) -> Watchlist:
        watchlist = self.watchlists.get_for_user(session, watchlist_id, user_id)
        if watchlist is None:
            raise NotFoundError("Watchlist was not found.")
        return watchlist

    def create_watchlist(self, session: Session, user_id: UUID, name: str) -> Watchlist:
        watchlist = Watchlist(user_id=user_id, name=name.strip())
        self.watchlists.add(session, watchlist)
        self._commit(session)
        return self.get_watchlist(session, user_id, watchlist.id)

    def rename_watchlist(
        self, session: Session, user_id: UUID, watchlist_id: UUID, name: str
    ) -> Watchlist:
        watchlist = self.get_watchlist(session, user_id, watchlist_id)
        watchlist.name = name.strip()
        self._commit(session)
        return self.get_watchlist(session, user_id, watchlist_id)

    def delete_watchlist(self, session: Session, user_id: UUID, watchlist_id: UUID) -> None:
        watchlist = self.get_watchlist(session, user_id, watchlist_id)
        self.watchlists.delete(session, watchlist)
        self._commit(session)

    def list_items(
        self, session: Session, user_id: UUID, watchlist_id: UUID
    ) -> list[WatchlistItem]:
        return self.get_watchlist(session, user_id, watchlist_id).items

    def add_item(
        self, session: Session, user_id: UUID, watchlist_id: UUID, symbol: str
    ) -> WatchlistItem:
        watchlist = self.get_watchlist(session, user_id, watchlist_id)
        instrument = self.instruments.get_by_symbol(session, symbol)
        if instrument is None:
            raise NotFoundError("Instrument was not found.")
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            instrument_id=instrument.id,
            position=self.watchlists.next_position(session, watchlist.id),
        )
        session.add(item)
        self._commit(session, duplicate_message="Instrument is already in this watchlist.")
        return self.watchlists.get_item_by_symbol(session, watchlist.id, instrument.symbol)  # type: ignore[return-value]

    def remove_item(self, session: Session, user_id: UUID, watchlist_id: UUID, symbol: str) -> None:
        watchlist = self.get_watchlist(session, user_id, watchlist_id)
        item = self.watchlists.get_item_by_symbol(session, watchlist.id, symbol)
        if item is None:
            raise NotFoundError("Instrument is not in this watchlist.")
        session.delete(item)
        self._commit(session)

    def reorder_items(
        self, session: Session, user_id: UUID, watchlist_id: UUID, symbols: list[str]
    ) -> list[WatchlistItem]:
        watchlist = self.get_watchlist(session, user_id, watchlist_id)
        current_by_symbol = {item.instrument.symbol: item for item in watchlist.items}
        requested = [symbol.upper() for symbol in symbols]
        validate_reorder(list(current_by_symbol), requested)
        for position, symbol in enumerate(requested, start=1):
            current_by_symbol[symbol].position = position
        self._commit(session)
        return [current_by_symbol[symbol] for symbol in requested]

    @staticmethod
    def _commit(session: Session, duplicate_message: str | None = None) -> None:
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            if duplicate_message:
                raise ConflictError(duplicate_message) from error
            raise
