from typing import Generator

from .database import SessionLocal


def get_db() -> Generator:
    """FastAPI dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
