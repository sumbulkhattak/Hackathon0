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
    tracker.record_failure("ORDER-1.md", "err")  # attempt 1: 30s * 2^1 = 60
    tracker.record_failure("ORDER-1.md", "err")  # attempt 2: 30s * 2^2 = 120
    tracker.record_failure("ORDER-1.md", "err")  # attempt 3: 30s * 2^3 = 240
    state = tracker.get_state("ORDER-1.md")
    assert state["attempts"] == 3
    assert state["backoff_seconds"] == 240


def test_backoff_capped_at_15_min(tracker):
    for _ in range(10):
        tracker.record_failure("ORDER-1.md", "err")
    state = tracker.get_state("ORDER-1.md")
    assert state["backoff_seconds"] <= 900  # 15 min


def test_should_skip_during_backoff(tracker):
    tracker.record_failure("ORDER-1.md", "err")
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
