import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import User
from app.schemas.attention import AttentionResponse
from app.schemas.market_data import DemoScenario
from app.services.market_data import MarketDataService


def attention_for(
    session: Session, service: MarketDataService, user: User
) -> list[AttentionResponse]:
    return asyncio.run(service.attention(session, user.id, ["TCS"]))


def test_meaningful_change_is_new_without_last_seen(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        user = User(display_name="New user", email="new-attention@example.test")
        session.add(user)
        session.commit()
        service = MarketDataService()
        service.select_scenario(user.id, DemoScenario.COMPANY_MOVE)

        result = attention_for(session, service, user)[0]

        assert result.is_new is True


def test_observation_timestamp_controls_is_new(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        user = User(display_name="Timing user", email="timing@example.test")
        session.add(user)
        session.commit()
        service = MarketDataService()
        service.select_scenario(user.id, DemoScenario.COMPANY_MOVE)

        user.last_market_check_at = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        session.commit()
        assert attention_for(session, service, user)[0].is_new is True

        user.last_market_check_at = datetime(2026, 9, 4, 10, 30, tzinfo=UTC)
        session.commit()
        assert attention_for(session, service, user)[0].is_new is False


def test_event_timestamp_controls_is_new(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        user = User(display_name="Event user", email="event@example.test")
        session.add(user)
        session.commit()
        service = MarketDataService()
        service.select_scenario(user.id, DemoScenario.COMPANY_MOVE)

        user.last_market_check_at = datetime(2026, 9, 4, 9, 10, tzinfo=UTC)
        session.commit()
        assert attention_for(session, service, user)[0].is_new is True

        user.last_market_check_at = datetime(2026, 9, 4, 10, 30, tzinfo=UTC)
        session.commit()
        assert attention_for(session, service, user)[0].is_new is False


def test_scenario_selection_changes_market_output(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        user = User(display_name="Scenario user", email="scenario@example.test")
        session.add(user)
        session.commit()
        service = MarketDataService()

        normal_quote = asyncio.run(service.quotes(user.id, ["TCS"]))[0]
        service.select_scenario(user.id, DemoScenario.COMPANY_MOVE)
        company_move_quote = asyncio.run(service.quotes(user.id, ["TCS"]))[0]

        assert company_move_quote.percentage_change != normal_quote.percentage_change


def test_new_update_is_new_after_company_move_is_marked_checked(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user = User(display_name="Lifecycle user", email="lifecycle@example.test")
        session.add(user)
        session.commit()
        service = MarketDataService()

        service.select_scenario(user.id, DemoScenario.COMPANY_MOVE)
        initial = attention_for(session, service, user)[0]
        assert initial.level.value in {"high", "moderate"}
        assert initial.is_new is True

        checked_at = service.mark_market_checked(session, user.id)
        assert attention_for(session, service, user)[0].is_new is False

        service.select_scenario(user.id, DemoScenario.NEW_UPDATE)
        follow_up = attention_for(session, service, user)[0]
        assert follow_up.latest_relevant_at > checked_at
        assert follow_up.level.value in {"high", "moderate"}
        assert follow_up.is_new is True


def test_attention_api_returns_last_seen_comparison_fields(client: TestClient) -> None:
    selected = client.post("/api/v1/demo/scenario", json={"scenario": "COMPANY_MOVE"})
    assert selected.status_code == 200

    response = client.get("/api/v1/market/attention?symbols=TCS")
    assert response.status_code == 200
    attention = response.json()[0]
    assert attention["isNew"] is True
    assert attention["latestRelevantAt"] == "2026-09-04T10:00:00Z"
