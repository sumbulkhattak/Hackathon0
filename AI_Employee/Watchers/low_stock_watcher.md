# Watcher: Low Stock Alert

> **Watcher ID:** low-stock
> **Type:** Event-driven
> **Trigger:** After every order is placed
> **Endpoint:** `POST /trigger/inventory`
> **Status:** ACTIVE

---

## Configuration

| Setting | Value |
|---------|-------|
| Threshold (Warning) | 10 units |
| Threshold (Critical) | 3 units |
| Threshold (Out of Stock) | 0 units |
| Check Scope | All products |
| Notify On | CRITICAL and OUT OF STOCK only |

## Behavior

1. After each order, check if any purchased product dropped below threshold
2. If CRITICAL or OUT OF STOCK:
   - Fire `/trigger/inventory` with the product ID
   - Task file created in `Needs_Action/`
   - Invoke `inventory-monitor` skill
3. If WARNING:
   - Log to `Logs/` only (no task created)
   - Include in daily report

## Deduplication

- Do not create duplicate alerts for the same product within 24 hours
- If product restocked and drops again, create new alert

## Log Format

```
[{timestamp}] WATCHER:low-stock | Product #{id} "{name}" | Stock: {n} | Level: {CRITICAL/WARNING/OK}
```
