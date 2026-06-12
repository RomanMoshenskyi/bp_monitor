"""Centralized structured logging configuration for bp_monitor.

Usage:
    from app.logging_config import get_logger
    log = get_logger(__name__)
    log.info("user_login", user_id=42, role="patient")
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_APP_LOG = _LOG_DIR / "app.log"
_ERR_LOG = _LOG_DIR / "errors.log"

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LOG_LEVEL = _LEVEL_MAP.get(
    os.environ.get("BP_LOG_LEVEL", "INFO").upper(), logging.INFO
)

_CONSOLE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_FILE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s %(funcName)s:%(lineno)d — %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _configure_root() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(_LOG_LEVEL)

    console = logging.StreamHandler()
    console.setLevel(_LOG_LEVEL)
    console.setFormatter(logging.Formatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    root.addHandler(console)

    rotating = logging.handlers.RotatingFileHandler(
        _APP_LOG, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    rotating.setLevel(_LOG_LEVEL)
    rotating.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(rotating)

    error_fh = logging.handlers.RotatingFileHandler(
        _ERR_LOG, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    error_fh.setLevel(logging.ERROR)
    error_fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(error_fh)


class _ContextLogger:
    """Thin wrapper that renders key=value pairs into the message string."""

    def __init__(self, logger: logging.Logger) -> None:
        self._log = logger

    def _fmt(self, msg: str, **kwargs) -> str:
        if not kwargs:
            return msg
        pairs = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        return f"{msg}  {pairs}"

    def debug(self, msg: str, **kwargs) -> None:
        self._log.debug(self._fmt(msg, **kwargs))

    def info(self, msg: str, **kwargs) -> None:
        self._log.info(self._fmt(msg, **kwargs))

    def warning(self, msg: str, **kwargs) -> None:
        self._log.warning(self._fmt(msg, **kwargs))

    def error(self, msg: str, **kwargs) -> None:
        self._log.error(self._fmt(msg, **kwargs))

    def critical(self, msg: str, **kwargs) -> None:
        self._log.critical(self._fmt(msg, **kwargs))

    def exception(self, msg: str, **kwargs) -> None:
        self._log.exception(self._fmt(msg, **kwargs))


_configure_root()


def get_logger(name: str) -> _ContextLogger:
    return _ContextLogger(logging.getLogger(name))
