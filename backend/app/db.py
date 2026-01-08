import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .models import Base

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL env var is not set.")
    return url

def make_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db() -> None:
    # MVP: create tables automatically.
    # Later: replace with Alembic migrations.
    Base.metadata.create_all(bind=engine)

def db_ping() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
