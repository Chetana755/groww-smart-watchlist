from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import User
from app.repositories.users import DEMO_USER_EMAIL
from app.services.market_data import MarketDataService


def test_new_user_has_no_last_market_check() -> None:
    user = User(display_name="New user", email="new@example.test")

    assert user.last_market_check_at is None


def test_marking_checked_persists_an_aware_timestamp(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user = User(display_name="Market user", email="market@example.test")
        session.add(user)
        session.commit()

        service = MarketDataService()
        first_check = service.mark_market_checked(session, user.id)
        second_check = service.mark_market_checked(session, user.id)

        assert first_check.tzinfo is not None
        assert first_check.utcoffset() == UTC.utcoffset(first_check)
        assert second_check >= first_check
        assert service.last_market_check_at(session, user.id) == second_check


def test_last_seen_api_returns_null_then_the_stored_timestamp(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    initial = client.get("/api/v1/market/last-seen")
    assert initial.status_code == 200
    assert initial.json() == {"lastSeenAt": None}

    marked = client.post("/api/v1/market/mark-checked")
    assert marked.status_code == 200
    marked_timestamp = datetime.fromisoformat(marked.json()["lastSeenAt"])
    assert marked_timestamp.tzinfo is not None

    stored = client.get("/api/v1/market/last-seen")
    assert stored.status_code == 200
    assert stored.json() == marked.json()

    with session_factory() as session:
        user = session.query(User).filter_by(email=DEMO_USER_EMAIL).one()
        assert user.last_market_check_at is not None
