---
id: 003
title: Create Retry Tracker
stage: green
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: hitl-approval-workflow
branch: master
user: user
command: task-implementation
labels: ["retry-tracker", "exponential-backoff", "tdd", "ralph-wiggum-loop"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/services/retry_tracker.py
  - backend/tests/test_retry_tracker.py
tests:
  - backend/tests/test_retry_tracker.py::test_new_task_not_blocked
  - backend/tests/test_retry_tracker.py::test_record_failure_increments_attempts
  - backend/tests/test_retry_tracker.py::test_backoff_increases_exponentially
  - backend/tests/test_retry_tracker.py::test_backoff_capped_at_15_min
  - backend/tests/test_retry_tracker.py::test_should_skip_during_backoff
  - backend/tests/test_retry_tracker.py::test_max_retries_exceeded
  - backend/tests/test_retry_tracker.py::test_max_retries_not_exceeded
  - backend/tests/test_retry_tracker.py::test_clear_removes_task
  - backend/tests/test_retry_tracker.py::test_get_all_returns_tracked_tasks
---

## Prompt

You are implementing Task 2: Create the retry tracker

## Task Description

**Files:**
- Create: `backend/services/retry_tracker.py`
- Create: `backend/tests/test_retry_tracker.py`

**Step 1: Write the failing test**
**Step 2: Run test to verify it fails**
**Step 3: Write minimal implementation**
**Step 4: Run test to verify it passes**
**Step 5: Commit**

Task 2 of 5. The retry tracker is used by the Ralph Wiggum Loop (Task 3) to handle transient failures with exponential backoff. Base backoff is 30s, doubles each attempt, caps at 15 minutes. After max_retries (default 5) the task is considered exhausted and moved to Rejected/.

## Response snapshot

Implemented the retry tracker service following TDD (red-green). Created test file with 9 tests covering: new task not blocked, failure recording increments attempts, exponential backoff calculation (30s * 2^attempts), backoff capped at 15 minutes (900s), should_skip during backoff window, max retries exhaustion detection, max retries not exceeded, clear removes task, and get_all returns all tracked tasks. Implementation uses in-memory dict storage with per-task state tracking (attempts, last_error, first_failed_at, next_retry_at, backoff_seconds). All 9 tests pass. Committed as c441306.

## Outcome

- Impact: Task 2 complete -- retry tracker ready for Task 3 (RalphWiggumLoop class)
- Tests: 9/9 passed
- Files: backend/services/retry_tracker.py, backend/tests/test_retry_tracker.py
- Next prompts: Task 3 -- Create RalphWiggumLoop class
- Reflection: Clean TDD cycle. The exponential backoff formula (BASE_BACKOFF * 2^attempts, capped at MAX_BACKOFF) is straightforward and well-tested. In-memory storage is appropriate since the loop restarts fresh on service restart.

## Evaluation notes (flywheel)

- Failure modes observed: None -- clean TDD cycle
- Graders run and results (PASS/FAIL): pytest PASS (9/9 retry_tracker tests)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement Task 3 (RalphWiggumLoop class) which consumes retry_tracker
