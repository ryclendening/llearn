from __future__ import annotations

import db.models  # noqa: F401 - imports model classes so SQLAlchemy metadata is populated.
from db.crud import seed_default_lesson
from db.session import Base, SessionLocal, engine


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_default_lesson(db)
