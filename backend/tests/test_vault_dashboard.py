"""Tests for vault dashboard — includes Executing and Archived counts."""
from services.vault import get_queue_counts


def test_queue_counts_includes_executing():
    counts = get_queue_counts()
    assert "Executing" in counts


def test_queue_counts_includes_archived():
    counts = get_queue_counts()
    assert "Archived" in counts
