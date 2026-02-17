"""Integration test — full HITL pipeline: PENDING -> COMPLETED."""
import pytest
from pathlib import Path
from unittest.mock import patch
from services.approval_guard import validate_transition
from services.task_mover import move_task


@pytest.fixture
def vault(tmp_path):
    dirs = {}
    for name in ["Needs_Action", "Pending_Approval", "Approved", "Executing", "Rejected", "Archived"]:
        d = tmp_path / name
        d.mkdir()
        dirs[name] = d
    return dirs


@pytest.fixture
def task_file(vault):
    content = """# Order Task

## Status: PENDING

| **Task Type** | ORDER |
| **Priority** | HIGH |
| **Customer** | Test Customer |

## Action Required
- [ ] Process order
"""
    path = vault["Needs_Action"] / "ORDER-TEST_2026-02-17_10-00-00.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_full_pipeline_happy_path(vault, task_file):
    """Task moves through all 5 stages: PENDING -> PROCESSED -> APPROVED -> EXECUTING -> COMPLETED."""

    # 1. PENDING -> PROCESSED (AI processes)
    validate_transition("PENDING", "PROCESSED", actor_type="ai")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Needs_Action", "Pending_Approval",
                      new_status="PROCESSED", actor="ai", actor_type="ai")

    assert (vault["Pending_Approval"] / "ORDER-TEST_2026-02-17_10-00-00.md").exists()
    assert not task_file.exists()

    # 2. PROCESSED -> APPROVED (Human approves)
    validate_transition("PROCESSED", "APPROVED", actor_type="human")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Pending_Approval", "Approved",
                      new_status="APPROVED", actor="admin", actor_type="human")

    assert (vault["Approved"] / "ORDER-TEST_2026-02-17_10-00-00.md").exists()

    # 3. APPROVED -> EXECUTING (System executes)
    validate_transition("APPROVED", "EXECUTING", actor_type="system")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Approved", "Executing",
                      new_status="EXECUTING", actor="executor", actor_type="system")

    assert (vault["Executing"] / "ORDER-TEST_2026-02-17_10-00-00.md").exists()

    # 4. EXECUTING -> COMPLETED (Success)
    validate_transition("EXECUTING", "COMPLETED", actor_type="system")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Executing", "Archived",
                      new_status="COMPLETED", actor="executor", actor_type="system")

    archived = vault["Archived"] / "ORDER-TEST_2026-02-17_10-00-00.md"
    assert archived.exists()
    content = archived.read_text(encoding="utf-8")
    assert "COMPLETED" in content


def test_rejection_reprocess_loop(vault, task_file):
    """Task rejected -> reprocessed -> re-enters pipeline."""

    # PENDING -> PROCESSED
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Needs_Action", "Pending_Approval",
                      new_status="PROCESSED", actor="ai", actor_type="ai")

    # PROCESSED -> REJECTED
    validate_transition("PROCESSED", "REJECTED", actor_type="human")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Pending_Approval", "Rejected",
                      new_status="REJECTED", actor="admin", actor_type="human")

    assert (vault["Rejected"] / "ORDER-TEST_2026-02-17_10-00-00.md").exists()

    # REJECTED -> PENDING (reprocess)
    validate_transition("REJECTED", "PENDING", actor_type="human")
    with patch("services.task_mover._resolve_dir", side_effect=lambda q: vault[q]):
        with patch("services.task_mover._audit_transition"):
            move_task("ORDER-TEST_2026-02-17_10-00-00.md",
                      "Rejected", "Needs_Action",
                      new_status="PENDING", actor="admin", actor_type="human")

    requeued = vault["Needs_Action"] / "ORDER-TEST_2026-02-17_10-00-00.md"
    assert requeued.exists()
    content = requeued.read_text(encoding="utf-8")
    assert "PENDING" in content
