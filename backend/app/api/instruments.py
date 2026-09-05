from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.repositories.instruments import InstrumentRepository
from app.schemas.instruments import InstrumentResponse

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("", response_model=list[InstrumentResponse])
def list_instruments(
    query: str | None = Query(default=None, max_length=100),
    session: Session = Depends(get_db_session),
) -> list[InstrumentResponse]:
    return InstrumentRepository().search(session, query)
