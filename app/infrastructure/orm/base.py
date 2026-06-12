"""SQLAlchemy ORM Base configuration."""
from __future__ import annotations

from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_database_url() -> str:
    """Build PostgreSQL connection URL from config."""
    # Simple URL without encoding - let psycopg2 handle it
    return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def create_engine_with_fallback():
    """Create engine with fallback for encoding issues."""
    try:
        url = get_database_url()
        return create_engine(url, pool_pre_ping=True)
    except Exception as e:
        print(f"Failed to create engine with URL: {e}")
        # Fallback: use DSN format
        dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
        return create_engine(f"postgresql+psycopg2:///?dsn={dsn}")


# Engine with connection pooling using connect_args to avoid encoding issues
try:
    # Use connect_args to pass parameters directly to psycopg2
    engine = create_engine(
        "postgresql+psycopg2://",
        connect_args={
            "host": DB_HOST,
            "port": int(DB_PORT) if DB_PORT else 5432,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": str(DB_PASSWORD) if DB_PASSWORD else "",
        },
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )
except Exception as e:
    print(f"Warning: Failed to create engine: {e}")
    # Ultimate fallback
    engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/bp_monitor",
        pool_pre_ping=True,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency injection helper for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
