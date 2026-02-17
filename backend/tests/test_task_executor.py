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
    assert calls[1] == ("Executing", "Pending_Approval")


def test_detect_task_type_from_filename():
    from services.task_executor import _detect_type
    assert _detect_type("ORDER-1_2026-02-17.md") == "ORDER"
    assert _detect_type("INQUIRY_2026-02-17.md") == "INQUIRY"
    assert _detect_type("INVENTORY-ALERT_2026-02-17.md") == "INVENTORY"
