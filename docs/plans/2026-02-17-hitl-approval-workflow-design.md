# Human-in-the-Loop Approval Workflow Design

**Date:** 2026-02-17
**Status:** Approved
**Approach:** File-System Native (Approach A)
**Policy:** Gate Everything — no action executes without human approval

---

## 1. State Machine

```
  TRIGGER
  (order, inquiry,           +----------------+
   inventory, file)     -->  | Needs_Action/  |  status: PENDING
                             +-------+--------+
                                     |
                            AI Process (Claude)
                                     |
                                     v
                        +------------------------+
                        |   Pending_Approval/    |  status: PROCESSED
                        |   (Human Review Gate)  |  or ESCALATED
                        |                        |
                        |  BLOCKED UNTIL         |
                        |  HUMAN DECIDES         |
                        +-----------+------------+
                               +----+----+
                               | HUMAN   |
                               | DECIDES |
                               +--+---+--+
                         APPROVE  |   |  REJECT
                                  |   |
                         +--------+   +--------+
                         v                     v
                +----------------+    +----------------+
                |  Approved/     |    |  Rejected/     |
                |  status:       |    |  status:       |
                |   APPROVED     |    |   REJECTED     |
                +-------+--------+    +-------+--------+
                        |                     |
                        v                     | (if reprocess=true)
                +----------------+            |
                |  Executing/    |            v
                |  status:       |    +----------------+
                |   EXECUTING    |    | Needs_Action/  |
                |                |    | (re-queued)    |
                +---+--------+--+    +----------------+
                    |        |
               SUCCESS    FAILURE
                    |        |
                    |        +--> Pending_Approval/
                    |             (retry with error context)
                    v
                +----------------+
                |  Archived/     |
                |  status:       |
                |   COMPLETED    |
                |  (read-only)   |
                +----------------+
```

### Valid State Transitions

| From Status | To Status | Actor |
|-------------|-----------|-------|
| PENDING | PROCESSED, ESCALATED | AI (system) |
| PROCESSED | APPROVED, REJECTED | Human only |
| ESCALATED | APPROVED, REJECTED | Human only |
| APPROVED | EXECUTING | System (after human triggered execute) |
| EXECUTING | COMPLETED | System (on success) |
| EXECUTING | PROCESSED | System (on failure, returns to Pending_Approval) |
| REJECTED | PENDING | Human (reprocess) |
| COMPLETED | *(terminal)* | — |

### Folder Map

| Status | Folder |
|--------|--------|
| PENDING | `Needs_Action/` |
| PROCESSED | `Pending_Approval/` |
| ESCALATED | `Pending_Approval/` |
| APPROVED | `Approved/` |
| EXECUTING | `Executing/` |
| REJECTED | `Rejected/` |
| COMPLETED | `Archived/` |

---

## 2. File Format & Metadata

Every task file uses YAML frontmatter to track its journey:

```yaml
---
id: ORDER-1
title: "Process Order #1 - Priya Sharma"
type: ORDER
priority: HIGH
status: APPROVED
created_at: 2026-02-17T10:30:00Z
created_by: trigger/order

# Processing
processed_at: 2026-02-17T10:31:15Z
processed_by: claude-opus-4-6
ai_confidence: 0.87
escalation: false

# Approval
approved_by: admin
approved_at: 2026-02-17T10:45:00Z
approval_notes: "Verified payment, ship today"

# Rejection (populated only if rejected)
rejected_by: null
rejected_at: null
rejection_reason: null
reprocess: false

# Execution
execution_started_at: null
execution_completed_at: null
execution_result: null
execution_error: null
failed_step: null

# Tracking
attempt_count: 1
folder_history:
  - { folder: "Needs_Action", entered: "2026-02-17T10:30:00Z" }
  - { folder: "Pending_Approval", entered: "2026-02-17T10:31:15Z" }
  - { folder: "Approved", entered: "2026-02-17T10:45:00Z" }
---
```

### Rules

- `status` must match the folder the file is in (enforced by move logic)
- `folder_history` is append-only — never edited, only added to
- Each reprocess increments `attempt_count`
- Rejection populates `rejected_by`, `rejection_reason`, `reprocess` fields
- Execution populates `execution_*` fields

---

## 3. Automation Logic — The Policy Guard

### 3.1 API Middleware (`approval_guard.py`)

Every state-changing endpoint passes through the guard:

| Endpoint | Required Status |
|----------|----------------|
| `POST /api/tasks/{id}/process` | PENDING |
| `POST /api/tasks/{id}/approve` | PROCESSED or ESCALATED |
| `POST /api/tasks/{id}/reject` | PROCESSED or ESCALATED |
| `POST /api/tasks/{id}/execute` | APPROVED *(new endpoint)* |
| `POST /api/tasks/{id}/reprocess` | REJECTED |

Invalid transitions return **403 Forbidden** with reason.

### 3.2 File Move Service (`task_mover.py`)

Write-then-delete pattern for safe file moves:

```
move_task(task_id, from_folder, to_folder):
  1. Read file from source
  2. Update frontmatter (status, timestamps, actor)
  3. Append to folder_history
  4. Write to destination folder
  5. Verify destination file exists and is valid
  6. Delete source file
  7. Log to audit trail

  On failure at any step -> rollback, log error, alert
```

### 3.3 Audit Logger (enhanced)

Every transition logs to both JSONL and Markdown:

```json
{
  "id": "evt-uuid",
  "timestamp": "2026-02-17T10:45:00Z",
  "action": "task.approved",
  "task_id": "ORDER-1",
  "task_type": "ORDER",
  "from_status": "PROCESSED",
  "to_status": "APPROVED",
  "from_folder": "Pending_Approval",
  "to_folder": "Approved",
  "actor": "admin",
  "actor_type": "human",
  "details": { "notes": "Verified payment, ship today" },
  "attempt": 1
}
```

New fields vs current: `from_status`, `to_status`, `from_folder`, `to_folder`, `actor_type` (human | system | ai).

---

## 4. Execution Engine & Failure Handling

### 4.1 Executor Service (`task_executor.py`)

Maps task types to concrete actions:

| Task Type | Action |
|-----------|--------|
| ORDER | Send confirmation email + dispatch |
| INQUIRY | Send reply email to customer |
| INVENTORY-ALERT | Create purchase order |
| FILE-UPLOAD | Classify + route document |
| EMAIL | Send email via SMTP/API |
| INVOICE | Generate + send invoice PDF |
| ESCALATION | Route to human owner |

### 4.2 Execution Flow

```
Approved/ORDER-1.md
    |
    +-- 1. Move to Executing/ (status: EXECUTING)
    +-- 2. Read action plan from AI output in file
    +-- 3. Execute steps sequentially
    |      +-- Step 1: Send confirmation email   OK
    |      +-- Step 2: Update order status in DB  OK
    |      +-- Step 3: Notify dispatch team       OK
    +-- 4. All succeeded -> Move to Archived/ (status: COMPLETED)
    |
    +-- ON FAILURE at any step:
         +-- Log which step failed + error message
         +-- Update frontmatter: execution_error, failed_step
         +-- Move back to Pending_Approval/ (status: PROCESSED)
         +-- Human sees: "Execution failed at step 2: DB timeout"
              +-- Can approve again to retry, or reject
```

### 4.3 Failure Policy

| Scenario | Behavior |
|----------|----------|
| Action succeeds | Move to `Archived/`, status: COMPLETED |
| Action fails (transient) | Back to `Pending_Approval/` with error context |
| Action partially completes | Back to `Pending_Approval/`, log completed steps |
| Executor crashes | Watchdog detects stale files (>15 min), moves back to `Pending_Approval/` |

### 4.4 Stale Execution Watchdog

- Runs every 5 minutes
- Any file in `Executing/` older than 15 minutes is assumed failed
- Moved back to `Pending_Approval/` with timeout error
- Logged to audit trail

---

## 5. Dashboard Integration

### Queue Filter Update

```
Queues: [ All | Needs Action | Pending Approval | Approved | Executing | Rejected | Archived ]
```

### Action Buttons Per State

| Folder | Actions |
|--------|---------|
| Needs_Action | **Process** |
| Pending_Approval | **Approve** / **Reject** |
| Approved | **Execute** |
| Executing | *(read-only, progress spinner)* |
| Rejected | **Reprocess** / **Delete** |
| Archived | *(read-only, view only)* |

### Overview Tab Additions

- Active executions count
- Last execution result (success/fail)
- Stale execution warnings (>15 min)

---

## 6. Complete Folder Structure

```
AI_Employee/
+-- Needs_Action/        # Inbox. New tasks land here. AI processes them.
+-- Pending_Approval/    # Gate. Human must approve or reject.
+-- Approved/            # Staging. Approved tasks awaiting execution.
+-- Executing/           # In-flight. Action being carried out.
+-- Rejected/            # Dead end or reprocess. Human feedback attached.
+-- Archived/            # Terminal. Completed tasks. Read-only.
+-- Plans/               # Reports from reasoning engine (unchanged)
+-- Logs/
|   +-- audit/           # JSONL audit trail
|   +-- LOG_{date}.md    # Human-readable daily log
+-- ...
```

---

## 7. Complete Rule Set

1. **No action without approval** — Every task passes through `Pending_Approval/` and requires explicit human approve/reject.
2. **Move files after decision** — Physical file moves between folders, tracked in `folder_history` frontmatter.
3. **Log all actions** — Every state transition logged to JSONL + Markdown audit trail with actor, timestamps, and context.
4. **No bypass** — API middleware rejects invalid transitions with 403.
5. **No silent failures** — Execution failures bounce back to human review with error context.
6. **Stale watchdog** — Files stuck in `Executing/` for >15 min auto-return to `Pending_Approval/`.

---

## 8. New Backend Files

| File | Purpose |
|------|---------|
| `backend/services/approval_guard.py` | State transition validator middleware |
| `backend/services/task_mover.py` | Safe file move with write-then-delete |
| `backend/services/task_executor.py` | Executes approved actions by task type |
| `backend/services/execution_watchdog.py` | Detects stale executions, returns to review |

### Modified Files

| File | Change |
|------|--------|
| `backend/routes/tasks.py` | Add `/execute` endpoint, integrate approval guard |
| `backend/services/audit_service.py` | Add `from_status`, `to_status`, `actor_type` fields |
| `frontend/src/app/ai-employee/page.tsx` | Add Executing/Archived filters, Execute button |
| `backend/config.py` | Add `EXECUTING_DIR`, `ARCHIVED_DIR` paths |
