import os
from configparser import ConfigParser
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "config.ini"

_DEFAULTS = {
    "host": "localhost",
    "port": "5432",
    "database": "bp_monitor",
    "user": "postgres",
    "password": "admin"
}


def _load_ini() -> dict[str, str]:
    if not CONFIG_FILE.exists():
        return {}
    parser = ConfigParser()
    parser.read(CONFIG_FILE, encoding="utf-8")
    if not parser.has_section("database"):
        return {}
    section = parser["database"]
    return {key: section.get(key, fallback="").strip() for key in _DEFAULTS}


def _build_db_config() -> dict[str, str]:
    ini = _load_ini()
    return {
        "host": os.getenv("DB_HOST", ini.get("host") or _DEFAULTS["host"]),
        "port": os.getenv("DB_PORT", ini.get("port") or _DEFAULTS["port"]),
        "database": os.getenv("DB_NAME", ini.get("database") or _DEFAULTS["database"]),
        "user": os.getenv("DB_USER", ini.get("user") or _DEFAULTS["user"]),
        "password": os.getenv("DB_PASSWORD", ini.get("password") or _DEFAULTS["password"]),
    }


DB_CONFIG = _build_db_config()

# Export individual variables for ORM compatibility
DB_HOST = DB_CONFIG["host"]
DB_PORT = DB_CONFIG["port"]
DB_NAME = DB_CONFIG["database"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]


def get_db_url() -> str:
    """Отримати URL для підключення до PostgreSQL"""
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


# Connection pool
POOL_MIN_CONN: int = int(os.getenv("BP_POOL_MIN", "1"))
POOL_MAX_CONN: int = int(os.getenv("BP_POOL_MAX", "10"))

# Logging
LOG_LEVEL: str = os.getenv("BP_LOG_LEVEL", "INFO").upper()

# Backup
BACKUP_DIR: Path = Path(os.getenv("BP_BACKUP_DIR", str(Path.home() / "bp_monitor_backups")))
BACKUP_KEEP_DAYS: int = int(os.getenv("BP_BACKUP_KEEP_DAYS", "30"))
