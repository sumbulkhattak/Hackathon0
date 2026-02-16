# Scheduled Task: Daily Revenue Summary

> **Task ID:** daily-revenue
> **Schedule:** Every day at 11:00 PM IST
> **Skill Used:** `daily-reporting`
> **Output:** `Plans/DAILY-REPORT_{YYYY-MM-DD}.md`
> **Status:** ACTIVE

---

## Execution

1. At 11:00 PM IST, pull today's order data from API
2. Calculate revenue, order count, average order value
3. Compare with yesterday and last week
4. Identify top-selling and zero-sale products
5. Generate report using `daily-reporting` skill
6. Save to `Plans/`
7. Update `Dashboard.md` metrics

## Dependencies

- Backend API must be reachable (`GET /api/stats`, `GET /api/orders`)
- Previous day's report for comparison data
