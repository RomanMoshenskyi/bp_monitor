from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Generator

import psycopg2
from psycopg2 import OperationalError, pool as pg_pool
from psycopg2.extensions import connection as PgConnection, cursor as PgCursor

from .config import DB_CONFIG, POOL_MAX_CONN, POOL_MIN_CONN
from .logging_config import get_logger

_log = get_logger(__name__)

# Уникаємо UnicodeDecodeError для кириличних повідомлень PostgreSQL на Windows.
os.environ.setdefault("PGCLIENTENCODING", "UTF8")


def _patch_psycopg2_unicode() -> None:
    """Wrap psycopg2._connect so CP1251 PostgreSQL error messages don't raise UnicodeDecodeError."""
    _orig = psycopg2._connect

    def _safe(dsn, connection_factory=None, **kw):
        try:
            return _orig(dsn, connection_factory=connection_factory, **kw)
        except UnicodeDecodeError as e:
            raw = getattr(e, "object", b"")
            try:
                msg = raw.decode("cp1251", errors="replace")
            except Exception:
                msg = raw.decode("latin-1", errors="replace")
            raise OperationalError(msg) from None

    psycopg2._connect = _safe


_patch_psycopg2_unicode()

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"

# ---------------------------------------------------------------------------
# Connection pool (double-checked locking, thread-safe)
# ---------------------------------------------------------------------------
_connection_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = Lock()

_POOL_CONNECT_KWARGS = {
    "connect_timeout": 5,
    "options": "-c client_encoding=UTF8",
}


def _build_pool() -> pg_pool.ThreadedConnectionPool:
    _log.info("pool_creating", min=POOL_MIN_CONN, max=POOL_MAX_CONN)
    return pg_pool.ThreadedConnectionPool(
        minconn=POOL_MIN_CONN,
        maxconn=POOL_MAX_CONN,
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        **_POOL_CONNECT_KWARGS,
    )


def get_connection_pool() -> pg_pool.ThreadedConnectionPool:
    global _connection_pool
    if _connection_pool is None or _connection_pool.closed:
        with _pool_lock:
            if _connection_pool is None or _connection_pool.closed:
                _connection_pool = _build_pool()
    return _connection_pool


def close_connection_pool() -> None:
    global _connection_pool
    if _connection_pool and not _connection_pool.closed:
        _connection_pool.closeall()
    _connection_pool = None


# ---------------------------------------------------------------------------
# Raw connect — used ONLY by init_schema / migrations (schema bootstrap)
# ---------------------------------------------------------------------------
def connect() -> PgConnection:
    try:
        return psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            **_POOL_CONNECT_KWARGS,
        )
    except UnicodeDecodeError:
        raise OperationalError(
            "Помилка підключення до PostgreSQL. "
            "Перевірте пароль у config.ini (секція [database]) або змінну DB_PASSWORD."
        ) from None


# ---------------------------------------------------------------------------
# Pool-based cursor context manager — use this everywhere in application code
# ---------------------------------------------------------------------------
@contextmanager
def db_cursor() -> Generator[PgCursor, None, None]:
    p = get_connection_pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def schema_initialized(conn: PgConnection) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'profile'
            )
            """
        )
        return bool(cur.fetchone()[0])


def init_schema(conn: PgConnection | None = None) -> None:
    own_conn = conn is None
    if own_conn:
        conn = connect()
    try:
        if not schema_initialized(conn):
            sql = SCHEMA_PATH.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
    finally:
        if own_conn and conn is not None:
            conn.close()

    from .migrations import run_migrations

    run_migrations(conn if not own_conn else None)
