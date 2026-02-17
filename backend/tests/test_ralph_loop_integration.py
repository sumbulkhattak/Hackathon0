"""Integration test — Ralph Wiggum Loop full cycle."""
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


def test_dry_run_cycle(vault_dirs):
    """Dry run processes nothing but reports correctly."""
    # Add a task to Needs_Action
    task = vault_dirs["Needs_Action"] / "ORDER-1_2026-02-17.md"
    task.write_text("# Task\n\n## Status: PENDING\n", encoding="utf-8")

    # Add a task to Approved
    approved = vault_dirs["Approved"] / "ORDER-2_2026-02-17.md"
    approved.write_text("# Task\n\n## Status: APPROVED\n", encoding="utf-8")

    loop = RalphWiggumLoop(poll_interval=1, max_retries=3, dry_run=True)

    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.NEEDS_ACTION_DIR = vault_dirs["Needs_Action"]
        mock_cfg.PENDING_APPROVAL_DIR = vault_dirs["Pending_Approval"]
        mock_cfg.APPROVED_DIR = vault_dirs["Approved"]
        mock_cfg.EXECUTING_DIR = vault_dirs["Executing"]
        with patch.object(loop, "phase_watchdog", return_value=[]):
            with patch.object(loop, "phase_status_heartbeat"):
                loop.cycle()

    assert loop.loop_count == 1
    # Files should still be in place (dry run)
    assert task.exists()
    assert approved.exists()


def test_retry_tracker_integration():
    """Retry tracker integrates with scan phase."""
    loop = RalphWiggumLoop(poll_interval=1, max_retries=2, dry_run=False)

    # Simulate 2 failures
    loop.retry_tracker.record_failure("ORDER-1.md", "API error")
    loop.retry_tracker.record_failure("ORDER-1.md", "API error")

    assert loop.retry_tracker.is_exhausted("ORDER-1.md") is True


def test_stop_halts_loop():
    """Calling stop() sets alive to False."""
    loop = RalphWiggumLoop(poll_interval=1)
    assert loop.alive is True
    loop.stop()
    assert loop.alive is False
