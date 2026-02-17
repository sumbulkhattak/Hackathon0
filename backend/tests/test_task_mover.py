"""Tests for task mover — safe write-then-delete file moves."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from services.task_mover import move_task, TaskMoveError


@pytest.fixture
def vault_dirs(tmp_path):
    """Create temporary vault directories."""
    dirs = {}
    for name in ["Needs_Action", "Pending_Approval", "Approved", "Executing", "Rejected", "Archived"]:
        d = tmp_path / name
        d.mkdir()
        dirs[name] = d
    return dirs


@pytest.fixture
def sample_task(vault_dirs):
    """Create a sample task file in Needs_Action."""
    content = "# Test Task\n\n## Status: PENDING\n\nSome content here."
    path = vault_dirs["Needs_Action"] / "ORDER-1_2026-02-17_10-00-00.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_move_task_writes_to_destination(vault_dirs, sample_task):
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault_dirs[q]):
        with patch("services.task_mover._audit_transition"):
            move_task(
                "ORDER-1_2026-02-17_10-00-00.md",
                "Needs_Action", "Pending_Approval",
                new_status="PROCESSED",
                actor="ai-employee",
                actor_type="ai",
            )
    dest = vault_dirs["Pending_Approval"] / "ORDER-1_2026-02-17_10-00-00.md"
    assert dest.exists()


def test_move_task_deletes_source(vault_dirs, sample_task):
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault_dirs[q]):
        with patch("services.task_mover._audit_transition"):
            move_task(
                "ORDER-1_2026-02-17_10-00-00.md",
                "Needs_Action", "Pending_Approval",
                new_status="PROCESSED",
                actor="ai-employee",
                actor_type="ai",
            )
    assert not sample_task.exists()


def test_move_task_updates_status_in_content(vault_dirs, sample_task):
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault_dirs[q]):
        with patch("services.task_mover._audit_transition"):
            move_task(
                "ORDER-1_2026-02-17_10-00-00.md",
                "Needs_Action", "Pending_Approval",
                new_status="PROCESSED",
                actor="ai-employee",
                actor_type="ai",
            )
    dest = vault_dirs["Pending_Approval"] / "ORDER-1_2026-02-17_10-00-00.md"
    content = dest.read_text(encoding="utf-8")
    assert "PROCESSED" in content


def test_move_task_source_not_found_raises(vault_dirs):
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault_dirs[q]):
        with pytest.raises(TaskMoveError, match="not found"):
            move_task(
                "NONEXISTENT.md",
                "Needs_Action", "Pending_Approval",
                new_status="PROCESSED",
                actor="ai-employee",
                actor_type="ai",
            )
