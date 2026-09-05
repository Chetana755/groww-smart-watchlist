from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.market_data import (
    DemoScenarioResponse,
    DemoScenarioSelectionRequest,
)
from app.services.market_data import market_data_service

router = APIRouter(prefix="/demo", tags=["demo"])
service = market_data_service


@router.get("/scenarios", response_model=list[DemoScenarioResponse])
def list_scenarios() -> list[DemoScenarioResponse]:
    return service.scenarios()


@router.get("/scenario", response_model=DemoScenarioResponse)
def get_scenario(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> DemoScenarioResponse:
    scenario = service.current_scenario(session, current_user.id)
    return next(item for item in service.scenarios() if item.scenario == scenario)


@router.post("/scenario", response_model=DemoScenarioResponse)
def select_scenario(
    request: DemoScenarioSelectionRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> DemoScenarioResponse:
    return service.select_scenario(session, current_user.id, request.scenario)
