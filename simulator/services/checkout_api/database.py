"""Database connection and session management for Checkout API."""

import logging
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from simulator.services.checkout_api.config import get_checkout_settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine():
    """Lazily initialize and return SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_checkout_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        elif "postgresql" in settings.database_url:
            connect_args["connect_timeout"] = 3
        
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def reset_engine(new_engine=None):
    """Reset cached engine and sessionmaker (used for testing or reconfiguration)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = new_engine
    _SessionLocal = None


def get_session_factory() -> sessionmaker:
    """Lazily initialize and return sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures closure."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined in models."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def check_db_health(db: Session) -> dict:
    """Execute simple query to verify database health and record round-trip latency."""
    start_time = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Database health check failed: {exc}")
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(exc),
        }
