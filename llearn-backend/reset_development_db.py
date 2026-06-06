from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from auth.config import APP_ENV
from db.session import Base, engine

import db.models  # noqa: F401


if __name__ == "__main__":
    if APP_ENV == "production":
        raise RuntimeError("Refusing to reset a production database.")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Development database reset complete.")
