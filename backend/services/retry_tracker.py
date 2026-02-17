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
