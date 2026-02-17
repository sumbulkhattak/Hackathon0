---
id: 002
title: Create Safe Task Mover Service
stage: green
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: hitl-approval-workflow
branch: master
user: user
command: task-implementation
labels: ["task-mover", "write-then-delete", "tdd", "hitl"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/services/task_mover.py
  - backend/tests/test_task_mover.py
tests:
  - backend/tests/test_task_mover.py::test_move_task_writes_to_destination
  - backend/tests/test_task_mover.py::test_move_task_deletes_source
  - backend/tests/test_task_mover.py::test_move_task_updates_status_in_content
  - backend/tests/test_task_mover.py::test_move_task_source_not_found_raises
---

## Prompt

You are implementing Task 3: Create safe task mover service (write-then-delete)

## Task Description

**Files:**
- Create: `backend/services/task_mover.py`
- Create: `backend/tests/test_task_mover.py`

**Step 1: Write the failing test**
**Step 2: Run test to verify it fails**
**Step 3: Write minimal implementation**
**Step 4: Run test to verify it passes**
**Step 5: Commit**

This is Task 3 of 10. The task mover is the file operation layer -- it handles the physical movement of task files between folders with a safe write-then-delete pattern. It depends on Task 1 (config.py has the new directory paths). It will be used by Task 4 (executor) and Task 5 (watchdog).

## Response snapshot

Implemented the safe task mover service following TDD (red-green). Created test file with 4 tests covering: writes to destination, deletes source, updates status in content, raises on missing source. All tests mock _resolve_dir and _audit_transition. Implementation uses write-then-delete pattern (write destination, verify, then delete source) instead of unsafe rename. Includes status line updates via regex, folder history tracking, and audit trail integration. All 23 tests pass (full suite including config and approval_guard). Committed as abc5232.

## Outcome

- Impact: Task 3 complete -- safe task mover service ready for Task 4 (executor) and Task 5 (watchdog)
- Tests: 4/4 passed, full suite 23/23 passed
- Files: backend/services/task_mover.py, backend/tests/test_task_mover.py
- Next prompts: Task 4 -- Create task executor service
- Reflection: Write-then-delete is safer than rename because it verifies the destination exists before deleting source, and gracefully handles delete failures without losing data.

## Evaluation notes (flywheel)

- Failure modes observed: None -- clean TDD cycle
- Graders run and results (PASS/FAIL): pytest PASS (4/4 task_mover, 23/23 full suite)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement Task 4 (task executor service) which consumes task_mover
