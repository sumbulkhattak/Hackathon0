# Ralph Wiggum Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a continuous polling loop that scans all 6 pipeline folders, processes tasks via Claude, pauses for human approval, executes approved tasks, recovers stale executions, updates memory, and reports status.

**Architecture:** Single `RalphWiggumLoop` class with 6 phases per cycle, exponential backoff retry tracker, graceful shutdown via signal handling. Reuses all existing HITL services (ai_processor, task_executor, execution_watchdog, task_mover, vault, audit).

**Tech Stack:** Python, existing FastAPI services, Claude API, filesystem polling

**Design Doc:** `docs/plans/2026-02-17-ralph-wiggum-loop-design.md`

---

### Task 1: Add loop config variables

**Files:**
- Modify: `backend/config.py:43-45`
- Test: `backend/tests/test_config.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_config.py`:

```python
def test_poll_interval_defined():
    assert hasattr(config, "POLL_INTERVAL")
    assert isinstance(config.POLL_INTERVAL, int)
    assert config.POLL_INTERVAL > 0


def test_max_retries_defined():
    assert hasattr(config, "MAX_RETRIES")
    assert isinstance(config.MAX_RETRIES, int)
    assert config.MAX_RETRIES > 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config.py::test_poll_interval_defined tests/test_config.py::test_max_retries_defined -v`
Expected: FAIL — attributes not found

**Step 3: Write minimal implementation**

Edit `backend/config.py` — add after line 45 (after `CLAUDE_MODEL`):

```python
# ── Ralph Wiggum Loop ───────────────────────────────────────────────────────
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))      # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add backend/config.py backend/tests/test_config.py
git commit -m "feat: add POLL_INTERVAL and MAX_RETRIES to config"
```

---

### Task 2: Create the retry tracker

**Files:**
- Create: `backend/services/retry_tracker.py`
- Create: `backend/tests/test_retry_tracker.py`

**Step 1: Write the failing test**

Create `backend/tests/test_retry_tracker.py`:

```python
"""Tests for retry tracker — exponential backoff for failed tasks."""
import pytest
import time
from services.retry_tracker import RetryTracker


@pytest.fixture
def tracker():
    return RetryTracker(max_retries=5)


def test_new_task_not_blocked(tracker):
    assert tracker.should_skip("ORDER-1.md") is False


def test_record_failure_increments_attempts(tracker):
    tracker.record_failure("ORDER-1.md", "API timeout")
    state = tracker.get_state("ORDER-1.md")
    assert state["attempts"] == 1
    assert state["last_error"] == "API timeout"


def test_backoff_increases_exponentially(tracker):
    tracker.record_failure("ORDER-1.md", "err")  # attempt 1: 30s
    tracker.record_failure("ORDER-1.md", "err")  # attempt 2: 60s
    tracker.record_failure("ORDER-1.md", "err")  # attempt 3: 120s
    state = tracker.get_state("ORDER-1.md")
    assert state["attempts"] == 3
    # backoff = min(2^3 * 30, 900) = 240
    assert state["backoff_seconds"] == 240


def test_backoff_capped_at_15_min(tracker):
    for _ in range(10):
        tracker.record_failure("ORDER-1.md", "err")
    state = tracker.get_state("ORDER-1.md")
    assert state["backoff_seconds"] <= 900  # 15 min


def test_should_skip_during_backoff(tracker):
    tracker.record_failure("ORDER-1.md", "err")
    # Immediately after failure, should be in backoff
    assert tracker.should_skip("ORDER-1.md") is True


def test_max_retries_exceeded(tracker):
    for i in range(5):
        tracker.record_failure("ORDER-1.md", f"err {i}")
    assert tracker.is_exhausted("ORDER-1.md") is True


def test_max_retries_not_exceeded(tracker):
    for i in range(3):
        tracker.record_failure("ORDER-1.md", f"err {i}")
    assert tracker.is_exhausted("ORDER-1.md") is False


def test_clear_removes_task(tracker):
    tracker.record_failure("ORDER-1.md", "err")
    tracker.clear("ORDER-1.md")
    assert tracker.should_skip("ORDER-1.md") is False
    assert tracker.get_state("ORDER-1.md") is None


def test_get_all_returns_tracked_tasks(tracker):
    tracker.record_failure("ORDER-1.md", "err1")
    tracker.record_failure("ORDER-2.md", "err2")
    all_states = tracker.get_all()
    assert len(all_states) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_retry_tracker.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/retry_tracker.py`:

```python
"""Retry Tracker — exponential backoff for failed task processing."""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE_BACKOFF = 30       # seconds
MAX_BACKOFF = 900       # 15 minutes


class RetryTracker:
    """Tracks failed tasks and enforces exponential backoff."""

    def __init__(self, max_retries: int = 5):
        self.max_retries = max_retries
        self._states: dict[str, dict] = {}

    def record_failure(self, task_id: str, error: str) -> None:
        """Record a failure for a task. Increments attempts and computes backoff."""
        state = self._states.get(task_id)
        if state is None:
            state = {
                "attempts": 0,
                "last_error": "",
                "first_failed_at": time.time(),
                "next_retry_at": 0.0,
                "backoff_seconds": 0,
            }
            self._states[task_id] = state

        state["attempts"] += 1
        state["last_error"] = error
        backoff = min(2 ** state["attempts"] * BASE_BACKOFF, MAX_BACKOFF)
        state["backoff_seconds"] = backoff
        state["next_retry_at"] = time.time() + backoff

        logger.warning(
            f"[RETRY] {task_id}: attempt {state['attempts']}/{self.max_retries}, "
            f"next retry in {backoff}s — {error}"
        )

    def should_skip(self, task_id: str) -> bool:
        """Return True if the task is in backoff and should not be processed yet."""
        state = self._states.get(task_id)
        if state is None:
            return False
        return time.time() < state["next_retry_at"]

    def is_exhausted(self, task_id: str) -> bool:
        """Return True if the task has exceeded max retries."""
        state = self._states.get(task_id)
        if state is None:
            return False
        return state["attempts"] >= self.max_retries

    def clear(self, task_id: str) -> None:
        """Remove a task from the tracker (e.g., after successful processing)."""
        self._states.pop(task_id, None)

    def get_state(self, task_id: str) -> Optional[dict]:
        """Get the retry state for a task, or None if not tracked."""
        return self._states.get(task_id)

    def get_all(self) -> dict[str, dict]:
        """Return all tracked task states."""
        return dict(self._states)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_retry_tracker.py -v`
Expected: PASS (all 9 tests)

**Step 5: Commit**

```bash
git add backend/services/retry_tracker.py backend/tests/test_retry_tracker.py
git commit -m "feat: add retry tracker with exponential backoff"
```

---

### Task 3: Create the Ralph Wiggum Loop class

**Files:**
- Create: `backend/ralph_loop.py`
- Create: `backend/tests/test_ralph_loop.py`

**Step 1: Write the failing test**

Create `backend/tests/test_ralph_loop.py`:

```python
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
        with patch("ralph_loop.process_task", return_value={"status": "processed"}):
            with patch("ralph_loop.move_task"):
                result = loop.phase_scan_and_process()
    # dry_run mode doesn't actually process
    assert isinstance(result, list)


def test_phase_execute_processes_approved(loop, vault_dirs):
    task = vault_dirs["Approved"] / "ORDER-1_2026-02-17.md"
    task.write_text("# Task\n\n## Status: APPROVED\n", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.APPROVED_DIR = vault_dirs["Approved"]
        with patch("ralph_loop.execute_task", return_value={"status": "COMPLETED", "filename": "ORDER-1_2026-02-17.md"}):
            result = loop.phase_execute()
    assert isinstance(result, list)


def test_phase_approval_gate_counts(loop, vault_dirs):
    for i in range(3):
        f = vault_dirs["Pending_Approval"] / f"TASK-{i}.md"
        f.write_text("pending", encoding="utf-8")
    with patch("ralph_loop.config") as mock_cfg:
        mock_cfg.PENDING_APPROVAL_DIR = vault_dirs["Pending_Approval"]
        count = loop.phase_approval_gate()
    assert count == 3
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_ralph_loop.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/ralph_loop.py`:

```python
"""
Ralph Wiggum Loop — The AI Employee's main event loop.

Continuously monitors all 6 pipeline folders:
  Phase 1: Scan Needs_Action/ → AI process → Pending_Approval/
  Phase 2: Approval gate (human decides, loop waits)
  Phase 3: Execute Approved/ → Executing/ → Archived/
  Phase 4: Watchdog — recover stale Executing/ tasks
  Phase 5: Memory update — sync client profiles
  Phase 6: Status heartbeat — dashboard + audit

Usage:
    python ralph_loop.py                  # Run forever, 30s interval
    python ralph_loop.py --interval 10    # Faster polling
    python ralph_loop.py --once           # Single cycle, then exit
    python ralph_loop.py --dry-run        # Log only, no writes
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import config
from config import ensure_vault_dirs
from services import vault, audit
from services.retry_tracker import RetryTracker
from services.task_executor import execute_task
from services.task_mover import move_task
from services.execution_watchdog import check_stale_executions

logger = logging.getLogger("ralph_loop")

SKIP_FILES = {"README.md"}


def _list_tasks(directory: Path) -> list[str]:
    """List .md task files in a directory, excluding README."""
    if not directory.exists():
        return []
    return [
        f.name for f in sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime)
        if f.name not in SKIP_FILES
    ]


def _extract_customer(content: str) -> dict:
    """Extract customer info from task file content."""
    import re
    customer = {}
    for field in ["Customer", "Email", "Phone", "Address"]:
        match = re.search(rf'\*\*{field}\*\*\s*\|\s*(.+?)\s*\|', content)
        if match:
            customer[field.lower()] = match.group(1).strip()
    return customer


class RalphWiggumLoop:
    """The AI Employee's main event loop."""

    def __init__(self, poll_interval: int = 30, max_retries: int = 5, dry_run: bool = False):
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.retry_tracker = RetryTracker(max_retries=max_retries)
        self.loop_count = 0
        self.alive = True
        self.start_time = time.time()
        # Cumulative stats
        self.total_processed = 0
        self.total_executed = 0
        self.total_failed = 0

    def run(self):
        """Main entry point. Blocks forever (or until stopped)."""
        ensure_vault_dirs()
        logger.info(
            f"Ralph Wiggum Loop started "
            f"(interval={self.poll_interval}s, max_retries={self.max_retries}, "
            f"dry_run={self.dry_run})"
        )
        while self.alive:
            self.loop_count += 1
            try:
                self.cycle()
            except Exception as e:
                logger.error(f"Cycle {self.loop_count} failed: {e}")
            if self.alive:
                time.sleep(self.poll_interval)
        logger.info("Ralph Wiggum Loop stopped.")

    def cycle(self):
        """One full scan of all folders."""
        logger.info(f"--- Cycle #{self.loop_count} ---")
        processed = self.phase_scan_and_process()
        self.phase_approval_gate()
        completed = self.phase_execute()
        self.phase_watchdog()
        self.phase_memory_update(completed)
        self.phase_status_heartbeat()

    def stop(self):
        """Graceful shutdown."""
        self.alive = False
        logger.info("Shutdown requested. Finishing current cycle...")

    # ── Phase 1: Scan & Process ──────────────────────────────────────────

    def phase_scan_and_process(self) -> list[str]:
        """Scan Needs_Action/ and AI-process each task."""
        tasks = _list_tasks(config.NEEDS_ACTION_DIR)
        processed = []

        for task_id in tasks:
            # Check retry backoff
            if self.retry_tracker.should_skip(task_id):
                logger.debug(f"[SCAN] Skipping {task_id} (in backoff)")
                continue

            # Check if exhausted
            if self.retry_tracker.is_exhausted(task_id):
                logger.warning(f"[SCAN] {task_id} exhausted retries, moving to Rejected/")
                if not self.dry_run:
                    try:
                        move_task(
                            task_id, "Needs_Action", "Rejected",
                            new_status="REJECTED",
                            actor="ralph-loop",
                            actor_type="system",
                            details={"reason": f"Max retries ({self.max_retries}) exceeded"},
                        )
                        self.retry_tracker.clear(task_id)
                    except Exception as e:
                        logger.error(f"[SCAN] Failed to reject {task_id}: {e}")
                continue

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would process: {task_id}")
                processed.append(task_id)
                continue

            # Process the task
            try:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    from services.ai_processor import process_task as ai_process
                    result = ai_process(task_id, db)
                    processed.append(task_id)
                    self.total_processed += 1
                    self.retry_tracker.clear(task_id)
                    logger.info(f"[SCAN] Processed: {task_id}")
                finally:
                    db.close()
            except Exception as e:
                error_msg = str(e)
                # Fatal error: auth failure — stop the loop
                if "401" in error_msg or "authentication" in error_msg.lower():
                    logger.critical(f"[SCAN] Auth failure — stopping loop: {e}")
                    self.alive = False
                    return processed
                # Transient error: record and retry later
                self.retry_tracker.record_failure(task_id, error_msg)
                self.total_failed += 1

        return processed

    # ── Phase 2: Approval Gate ───────────────────────────────────────────

    def phase_approval_gate(self) -> int:
        """Count pending approvals. Human decides — loop does nothing."""
        tasks = _list_tasks(config.PENDING_APPROVAL_DIR)
        count = len(tasks)
        if count > 0:
            logger.info(f"[GATE] Awaiting approval: {count} task(s)")
        return count

    # ── Phase 3: Execute ─────────────────────────────────────────────────

    def phase_execute(self) -> list[dict]:
        """Execute all approved tasks."""
        tasks = _list_tasks(config.APPROVED_DIR)
        completed = []

        for task_id in tasks:
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would execute: {task_id}")
                completed.append({"filename": task_id, "status": "DRY_RUN"})
                continue

            try:
                result = execute_task(task_id)
                completed.append(result)
                if result.get("status") == "COMPLETED":
                    self.total_executed += 1
                    logger.info(f"[EXEC] Completed: {task_id}")
                else:
                    self.total_failed += 1
                    logger.warning(f"[EXEC] Failed: {task_id} — {result.get('error', 'unknown')}")
            except Exception as e:
                self.total_failed += 1
                logger.error(f"[EXEC] Error executing {task_id}: {e}")

        return completed

    # ── Phase 4: Watchdog ────────────────────────────────────────────────

    def phase_watchdog(self) -> list[dict]:
        """Recover stale tasks from Executing/."""
        if self.dry_run:
            return []
        recovered = check_stale_executions()
        for r in recovered:
            logger.warning(f"[WATCHDOG] Recovered: {r['filename']}")
        return recovered

    # ── Phase 5: Memory Update ───────────────────────────────────────────

    def phase_memory_update(self, completed: list[dict]) -> None:
        """Update client memory for completed tasks."""
        if self.dry_run or not completed:
            return

        for task_result in completed:
            if task_result.get("status") != "COMPLETED":
                continue
            filename = task_result.get("filename", "")
            try:
                # Read the archived task to extract customer info
                content = vault.read_task_file("Archived", filename)
                customer = _extract_customer(content)
                if not customer.get("customer"):
                    continue

                slug = customer["customer"].lower().replace(" ", "-")
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                task_type = filename.split("_")[0].split("-")[0]

                try:
                    existing = vault.read_memory_file("Clients", f"{slug}.md")
                    entry = f"\n| {today} | {task_type} | {filename} — COMPLETED |"
                    vault.write_memory_file("Clients", f"{slug}.md", existing + entry)
                except FileNotFoundError:
                    new_profile = f"""# Client: {customer.get('customer', 'Unknown')}

| Field | Value |
|-------|-------|
| **Email** | {customer.get('email', '—')} |
| **Phone** | {customer.get('phone', '—')} |

## Interaction History

| Date | Type | Summary |
|------|------|---------|
| {today} | {task_type} | {filename} — COMPLETED |
"""
                    vault.write_memory_file("Clients", f"{slug}.md", new_profile)
                logger.info(f"[MEMORY] Updated: {slug}")
            except Exception as e:
                logger.warning(f"[MEMORY] Failed to update for {filename}: {e}")

    # ── Phase 6: Status Heartbeat ────────────────────────────────────────

    def phase_status_heartbeat(self) -> None:
        """Update dashboard and log heartbeat."""
        try:
            counts = vault.get_queue_counts()

            # Heartbeat audit entry
            audit.write_audit_entry(
                source="ralph-loop",
                action="loop.heartbeat",
                entity_type="system",
                entity_id=f"cycle-{self.loop_count}",
                actor="ralph-loop",
                details={
                    "cycle": self.loop_count,
                    "queues": counts,
                    "uptime_seconds": int(time.time() - self.start_time),
                    "totals": {
                        "processed": self.total_processed,
                        "executed": self.total_executed,
                        "failed": self.total_failed,
                    },
                    "retry_queue": len(self.retry_tracker.get_all()),
                },
                status="RUNNING",
            )

            # Refresh dashboard
            today = audit.get_today_summary()
            recent = audit.read_audit_entries()[-5:]
            vault.update_dashboard(
                queue_counts=counts,
                recent_actions=recent,
                today_metrics={
                    "completed": today.get("completed", 0),
                    "pending": today.get("pending", 0),
                    "inquiries": today.get("inquiries", 0),
                    "orders": today.get("orders", 0),
                    "alerts": today.get("alerts", 0),
                },
            )

            # Summary every 10th cycle
            if self.loop_count % 10 == 0:
                uptime = int(time.time() - self.start_time)
                retries = self.retry_tracker.get_all()
                logger.info(
                    f"\n{'='*50}\n"
                    f"Ralph Wiggum Loop — Cycle #{self.loop_count} Summary\n"
                    f"{'='*50}\n"
                    f"Uptime:          {uptime // 60}m {uptime % 60}s\n"
                    f"Total processed: {self.total_processed}\n"
                    f"Total executed:  {self.total_executed}\n"
                    f"Total failed:    {self.total_failed}\n"
                    f"Retry queue:     {len(retries)} task(s)\n"
                    f"---\n"
                    + "\n".join(f"  {q}: {c}" for q, c in counts.items())
                    + f"\n{'='*50}"
                )
        except Exception as e:
            logger.warning(f"[HEARTBEAT] Failed: {e}")


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop — AI Employee event loop")
    parser.add_argument("--interval", type=int, default=config.POLL_INTERVAL, help="Polling interval in seconds")
    parser.add_argument("--max-retries", type=int, default=config.MAX_RETRIES, help="Max retry attempts per task")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Log only, no writes")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    loop = RalphWiggumLoop(
        poll_interval=args.interval,
        max_retries=args.max_retries,
        dry_run=args.dry_run,
    )

    # Graceful shutdown
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}")
        loop.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if args.once:
        ensure_vault_dirs()
        loop.cycle()
        logger.info("Single cycle complete.")
    else:
        loop.run()


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_ralph_loop.py -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add backend/ralph_loop.py backend/tests/test_ralph_loop.py
git commit -m "feat: add Ralph Wiggum Loop — main AI Employee event loop"
```

---

### Task 4: Integration test — full loop cycle

**Files:**
- Create: `backend/tests/test_ralph_loop_integration.py`

**Step 1: Write the integration test**

```python
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
```

**Step 2: Run the integration test**

Run: `cd backend && python -m pytest tests/test_ralph_loop_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/test_ralph_loop_integration.py
git commit -m "test: add Ralph Wiggum Loop integration tests"
```

---

### Task 5: Run full test suite and finalize

**Step 1: Run all tests**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: Final commit**

```bash
git add -A
git commit -m "chore: finalize Ralph Wiggum Loop implementation"
```

---

## Summary

| Task | What | Files | Dependencies |
|------|------|-------|-------------|
| 1 | Config: POLL_INTERVAL, MAX_RETRIES | `config.py` | None |
| 2 | Retry tracker with exponential backoff | `services/retry_tracker.py` | None |
| 3 | RalphWiggumLoop class (6 phases + CLI) | `ralph_loop.py` | Tasks 1, 2 |
| 4 | Integration tests | `tests/test_ralph_loop_integration.py` | Task 3 |
| 5 | Full suite verification | — | All |
