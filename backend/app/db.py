import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL env var is not set.")
    return url

def make_engine() -> Engine:
    # future: add pooling config
    return create_engine(get_database_url(), pool_pre_ping=True)

engine = make_engine()

def db_ping() -> bool:
    """Returns True if DB is reachable and responsive."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
