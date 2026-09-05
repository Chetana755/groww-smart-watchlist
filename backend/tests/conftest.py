from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db_session
from app.db.base import Base
from app.main import app
from app.models.instrument import Instrument

CATALOG = [
    ("RELIANCE", "Reliance Industries Ltd.", "NSE", "Energy", "Oil & Gas Integrated"),
    ("TCS", "Tata Consultancy Services Ltd.", "NSE", "Information Technology", "IT Services"),
    ("INFY", "Infosys Ltd.", "NSE", "Information Technology", "IT Services"),
]


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        session.add_all(
            [
                Instrument(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=exchange,
                    sector=sector,
                    industry=industry,
                )
                for symbol, company_name, exchange, sector, industry in CATALOG
            ]
        )
        session.commit()
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient, None, None]:
    def override_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
