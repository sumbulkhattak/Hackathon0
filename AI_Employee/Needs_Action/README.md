# Needs Action

Tasks in this directory require AI processing.

## How It Works
1. Triggers (order, inquiry, inventory) create `.md` task files here
2. The AI Employee picks up tasks based on priority (CRITICAL > HIGH > MEDIUM > LOW)
3. After processing, tasks move to `Pending_Approval/`

## File Prefixes
| Prefix | Source | Skill |
|--------|--------|-------|
| `ORDER-` | Order placed | `order-processing` |
| `INQUIRY_` | Customer inquiry | `inquiry-reply` |
| `INVENTORY-ALERT_` | Low stock detected | `inventory-monitor` |
| `ESCALATION-` | Human escalation needed | Manual review |

## SLA
- CRITICAL tasks: Process within 1 hour
- HIGH tasks: Process within 4 hours
- MEDIUM tasks: Process within 12 hours
- LOW tasks: Process within 24 hours

> Tasks older than 24 hours are flagged as stale by the pending-review scheduled task.
