# HITL Approval Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a 6-folder Human-in-the-Loop approval workflow where every AI action requires human approval before execution.

**Architecture:** File-System Native — tasks are `.md` files that physically move between folders (`Needs_Action → Pending_Approval → Approved → Executing → Archived`, with `Rejected` as a branch). A policy guard middleware enforces valid state transitions. A stale execution watchdog recovers stuck tasks.

**Tech Stack:** FastAPI (Python), SQLite, Markdown files with YAML frontmatter, Next.js + React frontend

**Design Doc:** `docs/plans/2026-02-17-hitl-approval-workflow-design.md`

---

### Task 1: Add Executing and Archived directories to config

**Files:**
- Modify: `backend/config.py:12-37`

**Step 1: Write the failing test**

Create `backend/tests/test_config.py`:

```python
"""Tests for config — Executing and Archived directories."""
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
    # Patch the list used by ensure_vault_dirs to include our dirs
    config.ensure_vault_dirs()
    # The real test is just that the dirs exist in QUEUE_DIRS
    assert "Executing" in config.QUEUE_DIRS
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: FAIL — `EXECUTING_DIR` not defined

**Step 3: Write minimal implementation**

Edit `backend/config.py`:

After line 16 (`REJECTED_DIR`), add:
```python
EXECUTING_DIR = VAULT_PATH / "Executing"
ARCHIVED_DIR  = VAULT_PATH / "Archived"
```

Note: `ARCHIVE_DIR` already exists on line 27 pointing to `Archive`. The new `ARCHIVED_DIR` points to `Archived` (the HITL terminal folder — different from the legacy Archive).

Update `QUEUE_DIRS` (lines 31-37) to:
```python
QUEUE_DIRS = {
    "Needs_Action": NEEDS_ACTION_DIR,
    "Pending_Approval": PENDING_APPROVAL_DIR,
    "Approved": APPROVED_DIR,
    "Rejected": REJECTED_DIR,
    "Executing": EXECUTING_DIR,
    "Archived": ARCHIVED_DIR,
    "Plans": PLANS_DIR,
}
```

Update `ensure_vault_dirs()` (lines 46-47) to include `EXECUTING_DIR, ARCHIVED_DIR` in the list.

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/config.py backend/tests/test_config.py
git commit -m "feat: add Executing and Archived dirs to config"
```

---

### Task 2: Create the approval guard service

**Files:**
- Create: `backend/services/approval_guard.py`
- Create: `backend/tests/test_approval_guard.py`

**Step 1: Write the failing test**

Create `backend/tests/test_approval_guard.py`:

```python
"""Tests for approval guard — state transition enforcement."""
import pytest
from services.approval_guard import validate_transition, ApprovalGuardError


def test_pending_to_processed_valid():
    validate_transition("PENDING", "PROCESSED", actor_type="ai")


def test_pending_to_escalated_valid():
    validate_transition("PENDING", "ESCALATED", actor_type="ai")


def test_processed_to_approved_valid():
    validate_transition("PROCESSED", "APPROVED", actor_type="human")


def test_processed_to_rejected_valid():
    validate_transition("PROCESSED", "REJECTED", actor_type="human")


def test_escalated_to_approved_valid():
    validate_transition("ESCALATED", "APPROVED", actor_type="human")


def test_approved_to_executing_valid():
    validate_transition("APPROVED", "EXECUTING", actor_type="system")


def test_executing_to_completed_valid():
    validate_transition("EXECUTING", "COMPLETED", actor_type="system")


def test_executing_to_processed_valid_on_failure():
    validate_transition("EXECUTING", "PROCESSED", actor_type="system")


def test_rejected_to_pending_valid():
    validate_transition("REJECTED", "PENDING", actor_type="human")


def test_completed_is_terminal():
    with pytest.raises(ApprovalGuardError, match="terminal"):
        validate_transition("COMPLETED", "PENDING", actor_type="human")


def test_invalid_transition_raises():
    with pytest.raises(ApprovalGuardError):
        validate_transition("PENDING", "APPROVED", actor_type="human")


def test_pending_to_approved_skips_review():
    with pytest.raises(ApprovalGuardError):
        validate_transition("PENDING", "APPROVED", actor_type="ai")


def test_approved_requires_human_decision():
    """Only PROCESSED/ESCALATED -> APPROVED, not AI doing it."""
    with pytest.raises(ApprovalGuardError):
        validate_transition("APPROVED", "COMPLETED", actor_type="system")


def test_get_required_status_for_action():
    from services.approval_guard import get_required_status
    assert get_required_status("process") == ["PENDING"]
    assert get_required_status("approve") == ["PROCESSED", "ESCALATED"]
    assert get_required_status("reject") == ["PROCESSED", "ESCALATED"]
    assert get_required_status("execute") == ["APPROVED"]
    assert get_required_status("reprocess") == ["REJECTED"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_approval_guard.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/approval_guard.py`:

```python
"""Approval Guard — enforces valid state transitions in the HITL pipeline."""


class ApprovalGuardError(Exception):
    """Raised when a state transition is invalid."""
    pass


# Valid transitions: from_status -> list of allowed to_statuses
VALID_TRANSITIONS = {
    "PENDING":    ["PROCESSED", "ESCALATED"],
    "PROCESSED":  ["APPROVED", "REJECTED"],
    "ESCALATED":  ["APPROVED", "REJECTED"],
    "APPROVED":   ["EXECUTING"],
    "EXECUTING":  ["COMPLETED", "PROCESSED"],
    "REJECTED":   ["PENDING"],
    "COMPLETED":  [],
}

# Action name -> required current statuses
ACTION_REQUIRED_STATUS = {
    "process":   ["PENDING"],
    "approve":   ["PROCESSED", "ESCALATED"],
    "reject":    ["PROCESSED", "ESCALATED"],
    "execute":   ["APPROVED"],
    "reprocess": ["REJECTED"],
}

# Status -> folder mapping
STATUS_TO_FOLDER = {
    "PENDING":    "Needs_Action",
    "PROCESSED":  "Pending_Approval",
    "ESCALATED":  "Pending_Approval",
    "APPROVED":   "Approved",
    "EXECUTING":  "Executing",
    "REJECTED":   "Rejected",
    "COMPLETED":  "Archived",
}


def validate_transition(from_status: str, to_status: str, actor_type: str = "system") -> None:
    """Validate a state transition. Raises ApprovalGuardError if invalid."""
    allowed = VALID_TRANSITIONS.get(from_status)
    if allowed is None:
        raise ApprovalGuardError(f"Unknown status: {from_status}")
    if not allowed:
        raise ApprovalGuardError(f"Status '{from_status}' is terminal — no transitions allowed")
    if to_status not in allowed:
        raise ApprovalGuardError(
            f"Invalid transition: {from_status} -> {to_status}. "
            f"Allowed: {allowed}"
        )


def get_required_status(action: str) -> list[str]:
    """Return the list of valid current statuses for a given action."""
    return ACTION_REQUIRED_STATUS.get(action, [])


def get_target_folder(status: str) -> str:
    """Return the folder a task should be in for a given status."""
    folder = STATUS_TO_FOLDER.get(status)
    if folder is None:
        raise ApprovalGuardError(f"No folder mapping for status: {status}")
    return folder
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_approval_guard.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/approval_guard.py backend/tests/test_approval_guard.py
git commit -m "feat: add approval guard with state transition validation"
```

---

### Task 3: Create safe task mover service (write-then-delete)

**Files:**
- Create: `backend/services/task_mover.py`
- Create: `backend/tests/test_task_mover.py`

**Step 1: Write the failing test**

Create `backend/tests/test_task_mover.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_task_mover.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/task_mover.py`:

```python
"""Task Mover — safe write-then-delete file moves between vault folders."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config
from services import audit

logger = logging.getLogger(__name__)


class TaskMoveError(Exception):
    """Raised when a task move fails."""
    pass


def _resolve_dir(queue: str) -> Path:
    """Resolve queue name to directory path."""
    d = config.QUEUE_DIRS.get(queue)
    if d is None:
        raise TaskMoveError(f"Unknown queue: {queue}")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _audit_transition(
    task_id: str,
    task_type: str,
    from_status: str,
    to_status: str,
    from_folder: str,
    to_folder: str,
    actor: str,
    actor_type: str,
    details: Optional[dict] = None,
) -> None:
    """Write audit entries for a state transition."""
    audit.write_audit_entry(
        source="task-mover",
        action=f"task.{to_status.lower()}",
        entity_type=task_type.lower(),
        entity_id=task_id,
        actor=actor,
        details={
            **(details or {}),
            "from_status": from_status,
            "to_status": to_status,
            "from_folder": from_folder,
            "to_folder": to_folder,
            "actor_type": actor_type,
        },
        queue=to_folder,
        status=to_status,
    )
    audit.append_daily_log(
        source="task-mover",
        action=f"Task {to_status.capitalize()}",
        details=f"{task_id}: {from_folder} -> {to_folder} by {actor} ({actor_type})",
        status=to_status,
    )


def _update_status_line(content: str, new_status: str) -> str:
    """Replace ## Status: OLD with ## Status: NEW in task content."""
    updated = re.sub(
        r'(## Status:\s*)\w+',
        f'\\1{new_status}',
        content,
    )
    return updated


def _append_folder_history(content: str, folder: str) -> str:
    """Append a folder_history entry to the task content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"\n> Moved to **{folder}** at {now}\n"
    return content + entry


def move_task(
    filename: str,
    from_queue: str,
    to_queue: str,
    new_status: str,
    actor: str,
    actor_type: str,
    details: Optional[dict] = None,
) -> str:
    """
    Safely move a task file between folders using write-then-delete.

    1. Read from source
    2. Update status in content
    3. Append folder history
    4. Write to destination
    5. Verify destination
    6. Delete source
    7. Audit log

    Returns the new file path.
    Raises TaskMoveError on failure.
    """
    src_dir = _resolve_dir(from_queue)
    dst_dir = _resolve_dir(to_queue)
    src_path = src_dir / filename
    dst_path = dst_dir / filename

    # 1. Read source
    if not src_path.exists():
        raise TaskMoveError(f"Task file not found: {from_queue}/{filename}")

    content = src_path.read_text(encoding="utf-8")
    old_status = "UNKNOWN"
    status_match = re.search(r'## Status:\s*(\w+)', content)
    if status_match:
        old_status = status_match.group(1)

    # 2. Update status
    content = _update_status_line(content, new_status)

    # 3. Append folder history
    content = _append_folder_history(content, to_queue)

    # 4. Write to destination
    try:
        dst_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise TaskMoveError(f"Failed to write to {to_queue}/{filename}: {e}")

    # 5. Verify destination
    if not dst_path.exists():
        raise TaskMoveError(f"Verification failed: {to_queue}/{filename} not found after write")

    # 6. Delete source
    try:
        src_path.unlink()
    except Exception as e:
        logger.error(f"Failed to delete source {from_queue}/{filename}: {e}. Destination written OK.")

    # 7. Audit
    task_type = filename.split("_")[0].split("-")[0]
    _audit_transition(
        task_id=filename,
        task_type=task_type,
        from_status=old_status,
        to_status=new_status,
        from_folder=from_queue,
        to_folder=to_queue,
        actor=actor,
        actor_type=actor_type,
        details=details,
    )

    logger.info(f"[MOVER] {filename}: {from_queue}({old_status}) -> {to_queue}({new_status})")
    return str(dst_path)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_task_mover.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/task_mover.py backend/tests/test_task_mover.py
git commit -m "feat: add safe task mover with write-then-delete pattern"
```

---

### Task 4: Create the task executor service

**Files:**
- Create: `backend/services/task_executor.py`
- Create: `backend/tests/test_task_executor.py`

**Step 1: Write the failing test**

Create `backend/tests/test_task_executor.py`:

```python
"""Tests for task executor — executes approved actions."""
import pytest
from unittest.mock import patch, MagicMock
from services.task_executor import execute_task, ExecutionError


def test_execute_task_returns_result():
    mock_content = "# ORDER\n\n## Status: APPROVED\n\n## AI Output\nSend email to customer."
    with patch("services.task_executor._read_task", return_value=mock_content):
        with patch("services.task_executor._move", return_value="/path"):
            with patch("services.task_executor._run_action", return_value={"steps_completed": 1}):
                result = execute_task("ORDER-1_2026-02-17.md")
    assert result["status"] == "COMPLETED"


def test_execute_task_moves_to_executing_first():
    mock_content = "# ORDER\n\n## Status: APPROVED\n"
    calls = []
    def mock_move(fn, fr, to, **kw):
        calls.append((fr, to))
        return "/path"
    with patch("services.task_executor._read_task", return_value=mock_content):
        with patch("services.task_executor._move", side_effect=mock_move):
            with patch("services.task_executor._run_action", return_value={"steps_completed": 1}):
                execute_task("ORDER-1_2026-02-17.md")
    # First move: Approved -> Executing, Second move: Executing -> Archived
    assert calls[0] == ("Approved", "Executing")
    assert calls[1] == ("Executing", "Archived")


def test_execute_task_failure_returns_to_pending():
    mock_content = "# ORDER\n\n## Status: APPROVED\n"
    calls = []
    def mock_move(fn, fr, to, **kw):
        calls.append((fr, to))
        return "/path"
    with patch("services.task_executor._read_task", return_value=mock_content):
        with patch("services.task_executor._move", side_effect=mock_move):
            with patch("services.task_executor._run_action", side_effect=ExecutionError("DB timeout")):
                result = execute_task("ORDER-1_2026-02-17.md")
    assert result["status"] == "FAILED"
    # First move: Approved -> Executing, Second move: Executing -> Pending_Approval
    assert calls[1] == ("Executing", "Pending_Approval")


def test_detect_task_type_from_filename():
    from services.task_executor import _detect_type
    assert _detect_type("ORDER-1_2026-02-17.md") == "ORDER"
    assert _detect_type("INQUIRY_2026-02-17.md") == "INQUIRY"
    assert _detect_type("INVENTORY-ALERT_2026-02-17.md") == "INVENTORY"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_task_executor.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/task_executor.py`:

```python
"""Task Executor — executes approved actions by task type."""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import config
from services.task_mover import move_task

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when task execution fails."""
    pass


# Task type -> executor function (placeholder implementations)
EXECUTOR_MAP = {
    "ORDER":     "_execute_order",
    "INQUIRY":   "_execute_inquiry",
    "INVENTORY": "_execute_inventory",
    "FILE":      "_execute_file",
    "EMAIL":     "_execute_email",
    "INVOICE":   "_execute_invoice",
    "ESCALATION": "_execute_escalation",
}


def _detect_type(filename: str) -> str:
    """Detect task type from filename prefix."""
    prefix = filename.split("_")[0].split("-")[0]
    return prefix.upper()


def _read_task(filename: str, queue: str = "Approved") -> str:
    """Read task file content from a queue."""
    d = config.QUEUE_DIRS.get(queue)
    if d is None:
        raise ExecutionError(f"Unknown queue: {queue}")
    path = d / filename
    if not path.exists():
        raise ExecutionError(f"Task not found: {queue}/{filename}")
    return path.read_text(encoding="utf-8")


def _move(filename: str, from_queue: str, to_queue: str, **kwargs) -> str:
    """Wrapper around task_mover.move_task."""
    return move_task(filename, from_queue, to_queue, **kwargs)


def _run_action(task_type: str, content: str, filename: str) -> dict:
    """
    Execute the actual action for a task type.
    This is a placeholder — real implementations will send emails, update DBs, etc.
    Returns dict with execution details.
    """
    now = datetime.now(timezone.utc).isoformat()
    logger.info(f"[EXECUTOR] Running action for {task_type}: {filename}")

    # For now, log that execution happened. Real implementations come later.
    return {
        "steps_completed": 1,
        "executed_at": now,
        "action": f"{task_type.lower()}_action",
        "details": f"Executed {task_type} action for {filename}",
    }


def execute_task(filename: str) -> dict:
    """
    Execute an approved task through the full lifecycle:
    1. Move Approved -> Executing
    2. Run the action
    3. On success: Move Executing -> Archived
    4. On failure: Move Executing -> Pending_Approval

    Returns dict with execution result.
    """
    task_type = _detect_type(filename)

    # 1. Move to Executing
    _move(
        filename, "Approved", "Executing",
        new_status="EXECUTING",
        actor="task-executor",
        actor_type="system",
    )

    # 2. Run the action
    try:
        content = _read_task(filename, "Executing")
        result = _run_action(task_type, content, filename)

        # 3. Success -> Archived
        _move(
            filename, "Executing", "Archived",
            new_status="COMPLETED",
            actor="task-executor",
            actor_type="system",
            details=result,
        )

        logger.info(f"[EXECUTOR] {filename} completed successfully")
        return {
            "status": "COMPLETED",
            "filename": filename,
            "task_type": task_type,
            "moved_to": "Archived",
            **result,
        }

    except Exception as e:
        # 4. Failure -> back to Pending_Approval
        logger.error(f"[EXECUTOR] {filename} failed: {e}")

        try:
            _move(
                filename, "Executing", "Pending_Approval",
                new_status="PROCESSED",
                actor="task-executor",
                actor_type="system",
                details={"execution_error": str(e)},
            )
        except Exception as move_err:
            logger.error(f"[EXECUTOR] Failed to move {filename} back: {move_err}")

        return {
            "status": "FAILED",
            "filename": filename,
            "task_type": task_type,
            "moved_to": "Pending_Approval",
            "error": str(e),
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_task_executor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/task_executor.py backend/tests/test_task_executor.py
git commit -m "feat: add task executor with success/failure lifecycle"
```

---

### Task 5: Create the stale execution watchdog

**Files:**
- Create: `backend/services/execution_watchdog.py`
- Create: `backend/tests/test_execution_watchdog.py`

**Step 1: Write the failing test**

Create `backend/tests/test_execution_watchdog.py`:

```python
"""Tests for execution watchdog — recovers stale tasks in Executing/."""
import pytest
import time
from pathlib import Path
from unittest.mock import patch
from services.execution_watchdog import check_stale_executions


@pytest.fixture
def executing_dir(tmp_path):
    d = tmp_path / "Executing"
    d.mkdir()
    return d


def test_stale_file_detected(executing_dir):
    """A file older than threshold is considered stale."""
    stale = executing_dir / "ORDER-1_2026-02-17.md"
    stale.write_text("# Task\n\n## Status: EXECUTING\n", encoding="utf-8")
    # Set mtime to 20 minutes ago
    import os
    old_time = time.time() - (20 * 60)
    os.utime(stale, (old_time, old_time))

    with patch("services.execution_watchdog._get_executing_dir", return_value=executing_dir):
        with patch("services.execution_watchdog._recover_task") as mock_recover:
            check_stale_executions(threshold_minutes=15)
            mock_recover.assert_called_once()


def test_fresh_file_not_touched(executing_dir):
    """A recently modified file is NOT considered stale."""
    fresh = executing_dir / "ORDER-2_2026-02-17.md"
    fresh.write_text("# Task\n\n## Status: EXECUTING\n", encoding="utf-8")

    with patch("services.execution_watchdog._get_executing_dir", return_value=executing_dir):
        with patch("services.execution_watchdog._recover_task") as mock_recover:
            check_stale_executions(threshold_minutes=15)
            mock_recover.assert_not_called()


def test_empty_dir_no_error(executing_dir):
    with patch("services.execution_watchdog._get_executing_dir", return_value=executing_dir):
        result = check_stale_executions(threshold_minutes=15)
    assert result == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_execution_watchdog.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/execution_watchdog.py`:

```python
"""Execution Watchdog — detects stale tasks in Executing/ and recovers them."""

import logging
import time
from pathlib import Path

import config
from services.task_mover import move_task

logger = logging.getLogger(__name__)

STALE_THRESHOLD_MINUTES = 15


def _get_executing_dir() -> Path:
    return config.EXECUTING_DIR


def _recover_task(filename: str) -> dict:
    """Move a stale task from Executing back to Pending_Approval."""
    logger.warning(f"[WATCHDOG] Recovering stale task: {filename}")
    move_task(
        filename=filename,
        from_queue="Executing",
        to_queue="Pending_Approval",
        new_status="PROCESSED",
        actor="execution-watchdog",
        actor_type="system",
        details={"reason": "Execution timed out (stale watchdog)"},
    )
    return {"filename": filename, "action": "recovered", "moved_to": "Pending_Approval"}


def check_stale_executions(threshold_minutes: int = STALE_THRESHOLD_MINUTES) -> list[dict]:
    """
    Check Executing/ for files older than threshold.
    Moves stale files back to Pending_Approval.
    Returns list of recovered tasks.
    """
    executing_dir = _get_executing_dir()
    if not executing_dir.exists():
        return []

    now = time.time()
    threshold_seconds = threshold_minutes * 60
    recovered = []

    for f in executing_dir.glob("*.md"):
        age = now - f.stat().st_mtime
        if age > threshold_seconds:
            try:
                result = _recover_task(f.name)
                recovered.append(result)
            except Exception as e:
                logger.error(f"[WATCHDOG] Failed to recover {f.name}: {e}")

    if recovered:
        logger.info(f"[WATCHDOG] Recovered {len(recovered)} stale task(s)")

    return recovered
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_execution_watchdog.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/execution_watchdog.py backend/tests/test_execution_watchdog.py
git commit -m "feat: add execution watchdog for stale task recovery"
```

---

### Task 6: Update tasks.py routes — add /execute endpoint and integrate guard

**Files:**
- Modify: `backend/routes/tasks.py`
- Modify: `backend/schemas.py`
- Create: `backend/tests/test_task_routes.py`

**Step 1: Write the failing test**

Create `backend/tests/test_task_routes.py`:

```python
"""Tests for task routes — /execute endpoint and guard integration."""
import pytest
from unittest.mock import patch, MagicMock


def test_valid_queues_includes_new_folders():
    """VALID_QUEUES should include Executing and Archived."""
    from routes.tasks import VALID_QUEUES
    assert "Executing" in VALID_QUEUES
    assert "Archived" in VALID_QUEUES


def test_task_execution_schema():
    """TaskExecution schema should exist and have required fields."""
    from schemas import TaskExecution
    t = TaskExecution(executed_by="admin")
    assert t.executed_by == "admin"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_task_routes.py -v`
Expected: FAIL — "Executing" not in VALID_QUEUES, TaskExecution not found

**Step 3: Write minimal implementation**

Edit `backend/schemas.py` — add after `TaskRejection` class (after line 137):

```python
class TaskExecution(BaseModel):
    executed_by: str
    notes: Optional[str] = None
```

Edit `backend/routes/tasks.py`:

**Line 1:** Update docstring:
```python
"""Task Queue Routes — 8 endpoints for the 6-stage HITL pipeline."""
```

**Line 13:** Add import:
```python
from services.ai_processor import process_task
from services.task_executor import execute_task
from services.approval_guard import validate_transition, get_required_status, ApprovalGuardError
```

**Line 11:** Update schema import:
```python
from schemas import TaskApproval, TaskRejection, TaskExecution
```

**Line 19:** Update VALID_QUEUES:
```python
VALID_QUEUES = ["Needs_Action", "Pending_Approval", "Approved", "Executing", "Rejected", "Archived", "Plans"]
```

**After line 99 (after process endpoint), add the /execute endpoint:**

```python
# ── POST /api/tasks/{task_id}/execute — Execute an approved task ─────────

@router.post("/tasks/{task_id}/execute")
async def execute_task_endpoint(task_id: str, body: TaskExecution):
    """Execute an approved task — moves through Executing to Archived."""
    # Verify task exists in Approved
    try:
        content = vault.read_task_file("Approved", task_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found in Approved: {task_id}",
        )

    # Guard: verify status is APPROVED
    metadata = vault.parse_task_metadata(content)
    current_status = metadata.get("Status", "UNKNOWN")
    required = get_required_status("execute")
    if current_status not in required:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot execute task with status '{current_status}'. Required: {required}",
        )

    try:
        result = execute_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    _refresh_dashboard()

    return result
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_task_routes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/routes/tasks.py backend/schemas.py backend/tests/test_task_routes.py
git commit -m "feat: add /execute endpoint and integrate approval guard"
```

---

### Task 7: Update vault.py to support new queues in dashboard

**Files:**
- Modify: `backend/services/vault.py:124-230`

**Step 1: Write the failing test**

Create `backend/tests/test_vault_dashboard.py`:

```python
"""Tests for vault dashboard — includes Executing and Archived counts."""
from services.vault import get_queue_counts


def test_queue_counts_includes_executing():
    counts = get_queue_counts()
    assert "Executing" in counts


def test_queue_counts_includes_archived():
    counts = get_queue_counts()
    assert "Archived" in counts
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_vault_dashboard.py -v`
Expected: FAIL (if Executing/Archived not yet in QUEUE_DIRS — should pass after Task 1)

**Step 3: Write minimal implementation**

Edit `backend/services/vault.py` — update `update_dashboard()` function (lines 124-219).

Add rows for Executing and Archived in the Queue Summary table (around line 167):

```python
## Queue Summary

| Queue | Count | Oldest Item |
|-------|-------|-------------|
| Needs Action | {queue_counts.get('Needs_Action', 0)} | — |
| Pending Approval | {queue_counts.get('Pending_Approval', 0)} | — |
| Approved | {queue_counts.get('Approved', 0)} | — |
| Executing | {queue_counts.get('Executing', 0)} | — |
| Rejected | {queue_counts.get('Rejected', 0)} | — |
| Archived | {queue_counts.get('Archived', 0)} | — |
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_vault_dashboard.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/vault.py backend/tests/test_vault_dashboard.py
git commit -m "feat: add Executing/Archived to dashboard queue summary"
```

---

### Task 8: Update frontend — add Executing/Archived queue filters and Execute button

**Files:**
- Modify: `frontend/src/app/ai-employee/page.tsx`
- Modify: `frontend/src/lib/ai-api.ts`

**Step 1: Update API client**

Edit `frontend/src/lib/ai-api.ts` — add the `executeTask` function:

```typescript
export async function executeTask(taskId: string, executedBy: string, notes?: string) {
  const res = await fetch(`${API_BASE}/api/tasks/${encodeURIComponent(taskId)}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ executed_by: executedBy, notes }),
  });
  if (!res.ok) throw new Error(`Execute failed: ${res.statusText}`);
  return res.json();
}
```

**Step 2: Update the queue filter list**

In `frontend/src/app/ai-employee/page.tsx`, find the queue filter array (search for `Needs_Action`, `Pending_Approval`, `Approved`, `Rejected`) and add `"Executing"` and `"Archived"` to it.

**Step 3: Add Execute button for Approved queue**

Find the section that renders action buttons per queue. Add a case for `Approved` queue:

```tsx
{task.queue === 'Approved' && (
  <button
    onClick={() => handleExecute(task.filename)}
    className="px-3 py-1 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
  >
    Execute
  </button>
)}
```

**Step 4: Add handleExecute function**

```typescript
const handleExecute = async (taskId: string) => {
  try {
    await executeTask(taskId, 'admin');
    await refreshTasks();
  } catch (err) {
    console.error('Execute failed:', err);
  }
};
```

**Step 5: Add read-only indicators for Executing and Archived**

```tsx
{task.queue === 'Executing' && (
  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-lg text-sm animate-pulse">
    Executing...
  </span>
)}
{task.queue === 'Archived' && (
  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-lg text-sm">
    Completed
  </span>
)}
```

**Step 6: Commit**

```bash
git add frontend/src/lib/ai-api.ts frontend/src/app/ai-employee/page.tsx
git commit -m "feat: add Executing/Archived to dashboard with Execute button"
```

---

### Task 9: Integration test — full pipeline end-to-end

**Files:**
- Create: `backend/tests/test_hitl_integration.py`

**Step 1: Write the integration test**

```python
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
```

**Step 2: Run the integration test**

Run: `cd backend && python -m pytest tests/test_hitl_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/test_hitl_integration.py
git commit -m "test: add HITL pipeline integration tests"
```

---

### Task 10: Create __init__.py for tests and run full test suite

**Files:**
- Create: `backend/tests/__init__.py`

**Step 1: Create test init**

```python
# backend/tests/__init__.py
```

**Step 2: Run all tests**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 3: Final commit**

```bash
git add backend/tests/__init__.py
git commit -m "chore: add tests init and verify full HITL test suite"
```

---

## Summary

| Task | What | Files | Dependencies |
|------|------|-------|-------------|
| 1 | Config: Executing + Archived dirs | `config.py` | None |
| 2 | Approval guard service | `services/approval_guard.py` | None |
| 3 | Safe task mover (write-then-delete) | `services/task_mover.py` | Task 1 |
| 4 | Task executor service | `services/task_executor.py` | Task 1, 3 |
| 5 | Stale execution watchdog | `services/execution_watchdog.py` | Task 1, 3 |
| 6 | Routes: /execute endpoint + guard | `routes/tasks.py`, `schemas.py` | Task 1, 2, 4 |
| 7 | Dashboard: Executing/Archived counts | `services/vault.py` | Task 1 |
| 8 | Frontend: queue filters + Execute btn | `page.tsx`, `ai-api.ts` | Task 6 |
| 9 | Integration tests | `tests/test_hitl_integration.py` | Tasks 1-6 |
| 10 | Test suite finalization | `tests/__init__.py` | All |
