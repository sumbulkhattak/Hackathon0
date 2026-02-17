# Ralph Wiggum Loop — Design Document

**Date:** 2026-02-17
**Status:** Approved
**Approach:** Polling Loop (Approach A)
**Autonomy:** Pause at approval gate — human decides via dashboard

---

## 1. Overview

The Ralph Wiggum Loop is the AI Employee's main event loop. It continuously monitors all 6 pipeline folders, processes new tasks via Claude, pauses at the approval gate for human decision, executes approved tasks, recovers stale executions, updates client memory, and reports status.

**One loop. Six phases. Runs forever.**

---

## 2. Pseudocode

```
RALPH WIGGUM LOOP

initialize:
    load config
    ensure all 6 folders exist
    set retry_tracker = {}
    set loop_count = 0
    log "Ralph Wiggum Loop started"

while alive:
    loop_count++

    PHASE 1: SCAN & PROCESS (Needs_Action/)
        tasks = list_md_files(Needs_Action/)
        for each task:
            if backoff not expired: skip
            try:
                ai_output = process_with_claude(task)
                append ai_output to task file
                move task -> Pending_Approval/ (status: PROCESSED)
            catch escalation:
                create ESCALATION file
                move original -> Pending_Approval/ (status: ESCALATED)
            catch error:
                retry_tracker[task].attempts++
                backoff = min(2^attempts * 30s, 15min)
                if attempts >= MAX_RETRIES:
                    move task -> Rejected/ (reason: max retries)

    PHASE 2: APPROVAL GATE (Pending_Approval/)
        DO NOTHING. Human decides via dashboard.
        pending = count(Pending_Approval/)
        if pending > 0: log "Awaiting approval: {pending} task(s)"

    PHASE 3: EXECUTE (Approved/)
        for each task in Approved/:
            move task -> Executing/ (status: EXECUTING)
            try:
                result = run_action(task.type, task.content)
                move task -> Archived/ (status: COMPLETED)
            catch error:
                move task -> Pending_Approval/ (status: PROCESSED)

    PHASE 4: WATCHDOG (Executing/)
        stale = files in Executing/ older than 15 min
        for each stale: move -> Pending_Approval/ (reason: timeout)

    PHASE 5: MEMORY UPDATE
        for each completed task this cycle:
            upsert Memory/Clients/{client_slug}.md

    PHASE 6: STATUS & HEARTBEAT
        refresh_dashboard(queue_counts)
        log_heartbeat(loop_count, counts)
        if loop_count % 10 == 0: log_summary()

    sleep(POLL_INTERVAL)
```

---

## 3. Retry & Failure Logic

### Retry Tracker

```python
retry_tracker = {
    "ORDER-3_2026-02-17.md": {
        "attempts": 2,
        "last_error": "Claude API timeout",
        "next_retry_at": "2026-02-17T14:05:00Z",
        "first_failed_at": "2026-02-17T14:00:00Z",
    }
}
```

### Backoff Schedule

| Attempt | Wait Time |
|---------|-----------|
| 1 | 30 seconds |
| 2 | 60 seconds |
| 3 | 120 seconds |
| 4 | 240 seconds |
| 5 | GIVE UP -> move to Rejected/ |

### Failure Categories

| Error Type | Action |
|------------|--------|
| Claude API timeout | Retry with backoff |
| Claude API 401 | STOP LOOP (config broken) |
| Claude API 429 | Retry with longer backoff |
| File read error | Retry once, then skip |
| File move error | Log + alert, don't retry |
| Escalation detected | Normal path (not a failure) |
| Max retries reached | Move to Rejected/ |

---

## 4. Implementation Architecture

### Single file: `backend/ralph_loop.py`

```python
class RalphWiggumLoop:
    def __init__(self, poll_interval=30, max_retries=5, dry_run=False):
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.retry_tracker = {}
        self.loop_count = 0
        self.alive = True

    def run(self):
        ensure_vault_dirs()
        while self.alive:
            self.loop_count += 1
            self.cycle()
            sleep(self.poll_interval)

    def cycle(self):
        processed  = self.phase_scan_and_process()
        self.phase_approval_gate()
        completed  = self.phase_execute()
        self.phase_watchdog()
        self.phase_memory_update(completed)
        self.phase_status_heartbeat()

    def stop(self):
        self.alive = False
```

### Phase-to-Service Mapping

| Phase | Reuses Existing |
|-------|-----------------|
| Scan & Process | `ai_processor.process_task()` |
| Approval Gate | Nothing (just counts) |
| Execute | `task_executor.execute_task()` |
| Watchdog | `execution_watchdog.check_stale_executions()` |
| Memory Update | `vault.write_memory_file()` |
| Status | `vault.update_dashboard()` + `audit.write_audit_entry()` |

### CLI Interface

```bash
python ralph_loop.py                  # Run forever, 30s interval
python ralph_loop.py --interval 10    # Faster polling
python ralph_loop.py --once           # Single cycle, then exit
python ralph_loop.py --dry-run        # Log only, no writes
```

### Graceful Shutdown

Catches SIGINT/SIGTERM, sets `self.alive = False`, finishes current cycle, then exits.

---

## 5. Status Tracking & Heartbeat

### Heartbeat (every cycle)

```json
{
    "action": "loop.heartbeat",
    "cycle": 47,
    "queues": {
        "Needs_Action": 0,
        "Pending_Approval": 2,
        "Approved": 0,
        "Executing": 0,
        "Rejected": 1,
        "Archived": 5
    },
    "this_cycle": {
        "processed": 0,
        "executed": 0,
        "recovered": 0,
        "failed": 0
    }
}
```

### Summary (every 10th cycle)

```
Ralph Wiggum Loop -- Cycle #50 Summary
Uptime:          25 minutes
Total processed: 8 tasks
Total executed:  5 tasks
Total failed:    1 task
Retry queue:     1 task (ORDER-5, attempt 3/5)
```

### Dashboard.md Additions

- Loop status: RUNNING / STOPPED
- Current cycle number
- Last heartbeat timestamp
- Retry queue count

---

## 6. Files

### New

| File | Purpose |
|------|---------|
| `backend/ralph_loop.py` | Main loop class + CLI entry point |
| `backend/tests/test_ralph_loop.py` | Unit tests for all 6 phases |

### Modified

| File | Change |
|------|--------|
| `backend/services/vault.py` | Add loop status fields to `update_dashboard()` |
| `backend/config.py` | Add `POLL_INTERVAL`, `MAX_RETRIES` config vars |

---

## 7. Rules

1. **Never auto-approve** -- Phase 2 is always a hard stop for human decision
2. **Never skip audit** -- Every phase logs to the audit trail
3. **Exponential backoff** -- Failed tasks don't spam Claude API
4. **Fatal errors kill the loop** -- 401 auth errors stop immediately
5. **Graceful shutdown** -- Always finish current cycle before exiting
6. **Single instance** -- Only one loop runs at a time (PID file or lock)
