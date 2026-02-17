"""Tests for task routes — /execute endpoint and guard integration."""
import pytest


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
