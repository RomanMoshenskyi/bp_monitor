"""Unit tests for BackupService — no database or filesystem side-effects."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.backup_service import BackupService


def _make_storage(tmp_path: Path):
    storage = MagicMock()
    storage.user.id = 1
    storage.load.return_value = {
        "profile": {"name": "Test"},
        "measurements": [],
    }
    return storage


@pytest.fixture
def backup_svc(tmp_path):
    storage = _make_storage(tmp_path)
    svc = BackupService(storage)
    svc._backup_dir = tmp_path / "backups"
    return svc


class TestCreateBackup:
    def test_creates_file(self, backup_svc, tmp_path):
        path = backup_svc.create_backup()
        assert path.exists()
        assert path.suffix == ".json"

    def test_file_contains_valid_json(self, backup_svc):
        path = backup_svc.create_backup()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "profile" in data
        assert "measurements" in data

    def test_filename_includes_user_id(self, backup_svc):
        path = backup_svc.create_backup()
        assert "backup_1_" in path.name


class TestPurgeOldBackups:
    def test_deletes_old_files(self, backup_svc, tmp_path):
        backup_svc._ensure_dir()
        old_file = backup_svc._backup_dir / "backup_1_20200101_000000.json"
        old_file.write_text("{}", encoding="utf-8")
        old_time = time.time() - (40 * 24 * 3600)
        import os
        os.utime(old_file, (old_time, old_time))

        deleted = backup_svc.purge_old_backups()
        assert deleted == 1
        assert not old_file.exists()

    def test_keeps_recent_files(self, backup_svc):
        path = backup_svc.create_backup()
        deleted = backup_svc.purge_old_backups()
        assert deleted == 0
        assert path.exists()

    def test_no_error_when_dir_missing(self, backup_svc, tmp_path):
        backup_svc._backup_dir = tmp_path / "nonexistent"
        assert backup_svc.purge_old_backups() == 0


class TestBackupAndPurge:
    def test_returns_path(self, backup_svc):
        path = backup_svc.backup_and_purge()
        assert path.exists()
