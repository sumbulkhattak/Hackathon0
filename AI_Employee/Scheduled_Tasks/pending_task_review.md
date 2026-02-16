# Scheduled Task: Pending Task Review

> **Task ID:** pending-review
> **Schedule:** Every 4 hours (6 AM, 10 AM, 2 PM, 6 PM, 10 PM IST)
> **Status:** ACTIVE

---

## Execution

1. Scan `Needs_Action/` for files older than 24 hours
2. Scan `Pending_Approval/` for files older than 48 hours
3. For stale Needs_Action items:
   - Escalate with `STALE-TASK` flag
   - Add note: "This task has been pending for over 24 hours"
4. For stale Pending_Approval items:
   - Send reminder to approver
   - Add note: "Awaiting human approval for over 48 hours"
5. Update Dashboard.md queue counts and oldest item dates
6. Log scan results

## Thresholds

| Queue | Stale After | Action |
|-------|------------|--------|
| Needs_Action | 24 hours | Escalate |
| Pending_Approval | 48 hours | Reminder |
| Rejected (unprocessed) | 72 hours | Archive |
