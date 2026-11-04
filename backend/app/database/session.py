"""
SQLAlchemy database session management for DebugGraph AI.
Supports PostgreSQL with SQLite fallback for standalone and test execution.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models import Base

logger = get_logger(__name__)


def get_database_url() -> str:
    """Determine effective database URL with SQLite fallback."""
    if settings.DATABASE_URL:
        url = settings.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    return "sqlite:///debuggraph_local.db"


# Create database engine
db_url = get_database_url()
is_sqlite = db_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {"connect_timeout": 5}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
except Exception as exc:
    logger.warning("Could not initialize primary database driver for %s: %s. Using SQLite.", db_url, exc)
    db_url = "sqlite:///debuggraph_local.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables idempotently."""
    global engine, SessionLocal, db_url
    try:
        # Test connectivity
        with engine.connect() as conn:
            pass
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully [url=%s]", db_url.split("@")[-1])
    except Exception as exc:
        logger.warning("Could not initialize tables on primary database: %s. Using local SQLite.", exc)
        db_url = "sqlite:///debuggraph_local.db"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for obtaining a database session outside request contexts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

