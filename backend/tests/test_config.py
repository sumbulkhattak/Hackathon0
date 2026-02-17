"""Tests for config -- Executing and Archived directories."""
import config


def test_executing_dir_defined():
    assert hasattr(config, "EXECUTING_DIR")
    assert str(config.EXECUTING_DIR).endswith("Executing")


def test_archived_dir_defined():
    assert hasattr(config, "ARCHIVED_DIR")
    assert str(config.ARCHIVED_DIR).endswith("Archived")


def test_queue_dirs_includes_executing():
    assert "Executing" in config.QUEUE_DIRS


def test_queue_dirs_includes_archived():
    assert "Archived" in config.QUEUE_DIRS


def test_ensure_vault_dirs_creates_executing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EXECUTING_DIR", tmp_path / "Executing")
    monkeypatch.setattr(config, "ARCHIVED_DIR", tmp_path / "Archived")
    config.ensure_vault_dirs()
    assert "Executing" in config.QUEUE_DIRS
