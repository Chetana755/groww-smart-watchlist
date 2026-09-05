from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.users import UserRepository


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(session: Session = Depends(get_db_session)) -> User:
    """Replace this demo-user resolver with real authentication in a later phase."""
    return UserRepository().get_or_create_demo_user(session)
