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
