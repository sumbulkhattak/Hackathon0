# Scheduled Task: Morning Stock Scan

> **Task ID:** morning-stock-scan
> **Schedule:** Every day at 9:00 AM IST
> **Skill Used:** `inventory-monitor`
> **Endpoint:** `POST /trigger/inventory` (threshold: 10)
> **Status:** ACTIVE

---

## Execution

1. At 9:00 AM IST, fire inventory trigger for all products
2. Generate low-stock report
3. If CRITICAL items found → create task in `Needs_Action/`
4. If only WARNING items → log and include in daily report
5. Update Dashboard.md queue counts

## Dependencies

- Backend API must be reachable (`POST /trigger/inventory`)
- Product stock data must be current
