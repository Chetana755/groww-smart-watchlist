from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import User
from app.models.watchlist import Watchlist


def create_watchlist(client: TestClient, name: str = "Long term") -> dict:
    response = client.post("/api/v1/watchlists", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_create_list_get_rename_and_delete_watchlist(client: TestClient) -> None:
    created = create_watchlist(client)
    watchlist_id = created["id"]
    assert created["name"] == "Long term"
    assert created["items"] == []

    listed = client.get("/api/v1/watchlists")
    assert listed.status_code == 200
    assert listed.json()[0]["itemCount"] == 0

    fetched = client.get(f"/api/v1/watchlists/{watchlist_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == watchlist_id

    renamed = client.patch(f"/api/v1/watchlists/{watchlist_id}", json={"name": "Core holdings"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Core holdings"

    deleted = client.delete(f"/api/v1/watchlists/{watchlist_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/watchlists/{watchlist_id}").status_code == 404


def test_add_remove_and_reorder_items(client: TestClient) -> None:
    watchlist_id = create_watchlist(client)["id"]
    first = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "TCS"})
    second = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "INFY"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert [first.json()["position"], second.json()["position"]] == [1, 2]

    reordered = client.put(
        f"/api/v1/watchlists/{watchlist_id}/items/reorder", json={"symbols": ["INFY", "TCS"]}
    )
    assert reordered.status_code == 200
    assert [item["instrument"]["symbol"] for item in reordered.json()] == ["INFY", "TCS"]

    removed = client.delete(f"/api/v1/watchlists/{watchlist_id}/items/INFY")
    assert removed.status_code == 204
    items = client.get(f"/api/v1/watchlists/{watchlist_id}/items")
    assert [item["instrument"]["symbol"] for item in items.json()] == ["TCS"]


def test_rejects_duplicate_invalid_instrument_and_invalid_reorder(client: TestClient) -> None:
    watchlist_id = create_watchlist(client)["id"]
    assert (
        client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "TCS"}).status_code
        == 201
    )

    duplicate = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "TCS"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"

    missing = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "UNKNOWN"})
    assert missing.status_code == 404

    invalid_reorder = client.put(
        f"/api/v1/watchlists/{watchlist_id}/items/reorder", json={"symbols": ["RELIANCE"]}
    )
    assert invalid_reorder.status_code == 422
    assert invalid_reorder.json()["error"]["code"] == "invalid_reorder"


def test_rejects_watchlist_owned_by_another_user(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        other_user = User(display_name="Other", email="other@example.test")
        session.add(other_user)
        session.flush()
        foreign_watchlist = Watchlist(user_id=other_user.id, name="Private")
        session.add(foreign_watchlist)
        session.commit()
        foreign_id = foreign_watchlist.id

    response = client.get(f"/api/v1/watchlists/{foreign_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_instrument_search_returns_catalog_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/instruments?query=tcs")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": response.json()[0]["id"],
            "symbol": "TCS",
            "companyName": "Tata Consultancy Services Ltd.",
            "exchange": "NSE",
            "sector": "Information Technology",
            "industry": "IT Services",
        }
    ]
