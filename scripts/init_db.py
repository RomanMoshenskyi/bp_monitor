"""Ініціалізація схеми PostgreSQL для застосунку моніторингу тиску."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import DB_CONFIG  # noqa: E402
from app.database import connect, init_schema  # noqa: E402


def main() -> None:
    print(
        f"Підключення до {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']} ..."
    )
    conn = connect()
    try:
        init_schema(conn)
        print("Схему успішно застосовано (таблиці profile, measurements).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
