"""Automated backup service.

Creates a timestamped JSON backup of all patient measurements and removes
old backups beyond the configured retention window.
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..config import BACKUP_DIR, BACKUP_KEEP_DAYS
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..storage import PostgresStorage

_log = get_logger(__name__)


class BackupService:
    """Creates and manages JSON backups of measurement data."""

    def __init__(self, storage: "PostgresStorage") -> None:
        self._storage = storage
        self._backup_dir = BACKUP_DIR
        self._keep_days = BACKUP_KEEP_DAYS
        self._lock = threading.Lock()

    def _ensure_dir(self) -> None:
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, patient_id: Optional[int] = None) -> Path:
        """Write a timestamped JSON backup; return the path to the created file."""
        self._ensure_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = patient_id or self._storage.user.id
        filename = self._backup_dir / f"backup_{uid}_{ts}.json"

        with self._lock:
            data = self._storage.load(patient_id)
            filename.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        _log.info("backup_created", path=str(filename), patient_id=uid)
        return filename

    def purge_old_backups(self, patient_id: Optional[int] = None) -> int:
        """Delete backup files older than BACKUP_KEEP_DAYS; return count deleted."""
        if not self._backup_dir.exists():
            return 0
        uid = patient_id or self._storage.user.id
        cutoff = datetime.now() - timedelta(days=self._keep_days)
        deleted = 0
        with self._lock:
            for f in self._backup_dir.glob(f"backup_{uid}_*.json"):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < cutoff:
                        f.unlink()
                        deleted += 1
                        _log.info("backup_purged", path=str(f))
                except OSError as exc:
                    _log.error("backup_purge_failed", path=str(f), error=str(exc))
        return deleted

    def backup_and_purge(self, patient_id: Optional[int] = None) -> Path:
        """Convenience method: create backup then purge old ones."""
        path = self.create_backup(patient_id)
        removed = self.purge_old_backups(patient_id)
        if removed:
            _log.info("backup_purge_summary", removed=removed)
        return path

    def schedule_daily(self, patient_id: Optional[int] = None) -> None:
        """Schedule a non-blocking daily backup at next midnight."""

        def _run():
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            delay = (next_midnight - now).total_seconds()
            timer = threading.Timer(delay, self._daily_job, args=(patient_id,))
            timer.daemon = True
            timer.start()
            _log.info("backup_scheduled", delay_hours=round(delay / 3600, 1))

        _run()

    def _daily_job(self, patient_id: Optional[int]) -> None:
        try:
            self.backup_and_purge(patient_id)
        except Exception as exc:
            _log.error("backup_daily_failed", error=str(exc))
        self.schedule_daily(patient_id)
