"""Tests for Ralph Wiggum Loop — main event loop."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from ralph_loop import RalphWiggumLoop


@pytest.fixture
def vault_dirs(tmp_path):
    dirs = {}
    for name in ["Needs_Action", "Pending_Approval", "Approved", "Executing", "Rejected", "Archived"]:
        d = tmp_path / name
        d.mkdir()
        dirs[name] = d
    return dirs


@pytest.fixture
def loop():
    return RalphWiggumLoop(poll_interval=1, max_retries=3, dry_run=True)


def test_loop_initializes(loop):
    assert loop.poll_interval == 1
    assert loop.max_retries == 3
    assert loop.dry_run is True
    assert loop.loop_count == 0
    assert loop.alive is True


def test_loop_stop(loop):
    loop.stop()
    assert loop.alive is False


def test_cycle_increments_count(loop):
    with patch.object(loop, "phase_scan_and_process", return_value=[]):
        with patch.object(loop, "phase_approval_gate"):
            with patch.object(loop, "phase_execute", return_value=[]):
                with patch.object(loop, "phase_watchdog"):
                    with patch.object(loop, "phase_memory_update"):
                        with patch.object(loop, "phase_status_heartbeat"):
                            loop.cycle()
    assert loop.loop_count == 1


def test_phase_scan_skips_readme(loop, vault_dirs):
    readme = vault_dirs["Needs_Action"] / "README.md"
    readme.write_text("# Inbox", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.NEEDS_ACTION_DIR = vault_dirs["Needs_Action"]
        result = loop.phase_scan_and_process()
    assert result == []


def test_phase_scan_finds_tasks(loop, vault_dirs):
    task = vault_dirs["Needs_Action"] / "ORDER-1_2026-02-17.md"
    task.write_text("# Task\n\n## Status: PENDING\n", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.NEEDS_ACTION_DIR = vault_dirs["Needs_Action"]
        result = loop.phase_scan_and_process()
    assert isinstance(result, list)
    assert len(result) == 1  # dry_run mode logs but includes in result


def test_phase_execute_processes_approved(loop, vault_dirs):
    task = vault_dirs["Approved"] / "ORDER-1_2026-02-17.md"
    task.write_text("# Task\n\n## Status: APPROVED\n", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.APPROVED_DIR = vault_dirs["Approved"]
        result = loop.phase_execute()
    assert isinstance(result, list)
    assert len(result) == 1  # dry_run returns DRY_RUN result


def test_phase_approval_gate_counts(loop, vault_dirs):
    for i in range(3):
        f = vault_dirs["Pending_Approval"] / f"TASK-{i}.md"
        f.write_text("pending", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.PENDING_APPROVAL_DIR = vault_dirs["Pending_Approval"]
        count = loop.phase_approval_gate()
    assert count == 3
