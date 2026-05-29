from __future__ import annotations

import db.models  # noqa: F401 - imports model classes so SQLAlchemy metadata is populated.
from db.crud import seed_default_lesson
from db.session import Base, SessionLocal, engine
from sqlalchemy import inspect, text


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_existing_table_columns()
    with SessionLocal() as db:
        seed_default_lesson(db)


def _ensure_existing_table_columns() -> None:
    inspector = inspect(engine)
    if "course_materials" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("course_materials")}
    statements = []
    if "extraction_status" not in existing_columns:
        statements.append("ALTER TABLE course_materials ADD COLUMN extraction_status VARCHAR(30) NOT NULL DEFAULT 'pending'")
    if "extraction_error" not in existing_columns:
        statements.append("ALTER TABLE course_materials ADD COLUMN extraction_error TEXT")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
