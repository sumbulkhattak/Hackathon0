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
