# Agent Configuration — Thresholds

> **Last Updated:** 2026-02-16
> **Scope:** All watchers and skills read these values at runtime.

---

## Inventory Thresholds

| Level | Units | Action |
|-------|-------|--------|
| OK | > 10 | Normal display |
| WARNING | 8–10 | Log only, include in daily report |
| LOW | 4–7 | Create task, standard restock (3-day SLA) |
| CRITICAL | 1–3 | Create task, emergency restock (24-hour SLA) |
| OUT_OF_STOCK | 0 | Immediate escalation, hide from website |

## SLA Timers

| Queue | Stale After | Action |
|-------|-------------|--------|
| Needs_Action — CRITICAL | 1 hour | Auto-escalate |
| Needs_Action — HIGH | 4 hours | Flag |
| Needs_Action — MEDIUM | 12 hours | Flag |
| Needs_Action — LOW | 24 hours | Flag |
| Pending_Approval | 48 hours | Send reminder |
| Rejected (unprocessed) | 72 hours | Archive |

## Response SLAs

| Channel | First Response | Resolution |
|---------|---------------|------------|
| Email Inquiry | 4 hours | 24 hours |
| Order Issue | 2 hours | 12 hours |
| Complaint | 1 hour | 6 hours |
| Social Media | 2 hours | 8 hours |

## Financial Thresholds

| Decision | AI Autonomous | Needs Approval |
|----------|---------------|----------------|
| Refund amount | < 500 | >= 500 |
| Discount application | Valid codes only | Custom discounts |
| Supplier reorder value | < 10,000 | >= 10,000 |
