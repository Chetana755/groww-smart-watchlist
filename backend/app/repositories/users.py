from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User

DEMO_USER_EMAIL = "demo.user@smartwatchlist.local"


class UserRepository:
    def get_by_id(self, session: Session, user_id: UUID) -> User | None:
        return session.get(User, user_id)

    def get_or_create_demo_user(self, session: Session) -> User:
        user = session.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
        if user is not None:
            return user

        user = User(display_name="Demo User", email=DEMO_USER_EMAIL)
        session.add(user)
        try:
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            # Two first requests can race on the unique demo email. The
            # request that loses the race re-reads the row created by the winner.
            session.rollback()
            existing = session.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
            if existing is None:
                raise
            return existing
