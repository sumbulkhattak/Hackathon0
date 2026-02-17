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
    with pytest.raises(ApprovalGuardError):
        validate_transition("APPROVED", "COMPLETED", actor_type="system")


def test_get_required_status_for_action():
    from services.approval_guard import get_required_status
    assert get_required_status("process") == ["PENDING"]
    assert get_required_status("approve") == ["PROCESSED", "ESCALATED"]
    assert get_required_status("reject") == ["PROCESSED", "ESCALATED"]
    assert get_required_status("execute") == ["APPROVED"]
    assert get_required_status("reprocess") == ["REJECTED"]
