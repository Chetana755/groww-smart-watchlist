from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.market_data import DemoScenarioResponse, DemoScenarioSelectionRequest
from app.services.market_data import market_data_service

router = APIRouter(prefix="/demo", tags=["demo"])
service = market_data_service

@router.get("/scenarios", response_model=list[DemoScenarioResponse])
def list_scenarios() -> list[DemoScenarioResponse]:
    return service.scenarios()


@router.post("/scenario", response_model=DemoScenarioResponse)
def select_scenario(
    request: DemoScenarioSelectionRequest, current_user: User = Depends(get_current_user)
) -> DemoScenarioResponse:
    return service.select_scenario(current_user.id, request.scenario)
