from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.watchlists import (
    ReorderWatchlistItemsRequest,
    WatchlistCreateRequest,
    WatchlistItemCreateRequest,
    WatchlistItemResponse,
    WatchlistResponse,
    WatchlistSummaryResponse,
    WatchlistUpdateRequest,
)
from app.services.watchlists import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"])
service = WatchlistService()


def as_summary(watchlist: object) -> WatchlistSummaryResponse:
    return WatchlistSummaryResponse.model_validate(
        {
            "id": watchlist.id,
            "name": watchlist.name,
            "created_at": watchlist.created_at,
            "updated_at": watchlist.updated_at,
            "item_count": len(watchlist.items),
        }
    )


@router.get("", response_model=list[WatchlistSummaryResponse])
def list_watchlists(
    session: Session = Depends(get_db_session), current_user: User = Depends(get_current_user)
) -> list[WatchlistSummaryResponse]:
    return [
        as_summary(watchlist) for watchlist in service.list_watchlists(session, current_user.id)
    ]


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    request: WatchlistCreateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WatchlistResponse:
    return service.create_watchlist(session, current_user.id, request.name)


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(
    watchlist_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WatchlistResponse:
    return service.get_watchlist(session, current_user.id, watchlist_id)


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(
    watchlist_id: UUID,
    request: WatchlistUpdateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WatchlistResponse:
    return service.rename_watchlist(session, current_user.id, watchlist_id, request.name)


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    service.delete_watchlist(session, current_user.id, watchlist_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{watchlist_id}/items", response_model=list[WatchlistItemResponse])
def list_watchlist_items(
    watchlist_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[WatchlistItemResponse]:
    return service.list_items(session, current_user.id, watchlist_id)


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_watchlist_item(
    watchlist_id: UUID,
    request: WatchlistItemCreateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WatchlistItemResponse:
    return service.add_item(session, current_user.id, watchlist_id, request.symbol)


@router.delete("/{watchlist_id}/items/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist_item(
    watchlist_id: UUID,
    symbol: str,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    service.remove_item(session, current_user.id, watchlist_id, symbol)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{watchlist_id}/items/reorder", response_model=list[WatchlistItemResponse])
def reorder_watchlist_items(
    watchlist_id: UUID,
    request: ReorderWatchlistItemsRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[WatchlistItemResponse]:
    return service.reorder_items(session, current_user.id, watchlist_id, request.symbols)
