"""Approval Guard — enforces valid state transitions in the HITL pipeline."""


class ApprovalGuardError(Exception):
    """Raised when a state transition is invalid."""
    pass


VALID_TRANSITIONS = {
    "PENDING":    ["PROCESSED", "ESCALATED"],
    "PROCESSED":  ["APPROVED", "REJECTED"],
    "ESCALATED":  ["APPROVED", "REJECTED"],
    "APPROVED":   ["EXECUTING"],
    "EXECUTING":  ["COMPLETED", "PROCESSED"],
    "REJECTED":   ["PENDING"],
    "COMPLETED":  [],
}

ACTION_REQUIRED_STATUS = {
    "process":   ["PENDING"],
    "approve":   ["PROCESSED", "ESCALATED"],
    "reject":    ["PROCESSED", "ESCALATED"],
    "execute":   ["APPROVED"],
    "reprocess": ["REJECTED"],
}

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
    allowed = VALID_TRANSITIONS.get(from_status)
    if allowed is None:
        raise ApprovalGuardError(f"Unknown status: {from_status}")
    if not allowed:
        raise ApprovalGuardError(f"Status '{from_status}' is terminal — no transitions allowed")
    if to_status not in allowed:
        raise ApprovalGuardError(
            f"Invalid transition: {from_status} -> {to_status}. Allowed: {allowed}"
        )


def get_required_status(action: str) -> list[str]:
    return ACTION_REQUIRED_STATUS.get(action, [])


def get_target_folder(status: str) -> str:
    folder = STATUS_TO_FOLDER.get(status)
    if folder is None:
        raise ApprovalGuardError(f"No folder mapping for status: {status}")
    return folder
