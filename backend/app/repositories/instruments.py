from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.instrument import Instrument


class InstrumentRepository:
    def search(self, session: Session, query: str | None) -> list[Instrument]:
        statement: Select[tuple[Instrument]] = select(Instrument).order_by(Instrument.symbol)
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(Instrument.symbol.ilike(pattern), Instrument.company_name.ilike(pattern))
            )
        return list(session.scalars(statement.limit(20)))

    def get_by_symbol(self, session: Session, symbol: str) -> Instrument | None:
        return session.scalar(select(Instrument).where(Instrument.symbol == symbol.upper()))
