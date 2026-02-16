# Skill: Daily Reporting

> **Skill ID:** daily-reporting
> **Trigger:** Scheduled — 11:00 PM IST daily
> **Priority:** Low
> **Output:** `Plans/DAILY-REPORT_{date}.md`

---

## Purpose

Compile end-of-day business metrics into a structured report for management review.

## Steps

### 1. Collect Metrics

**Revenue:**
- Total revenue today
- Comparison to yesterday (% change)
- Comparison to same day last week
- Running monthly total

**Orders:**
- New orders today
- Orders confirmed
- Orders shipped
- Orders delivered
- Orders cancelled/returned
- Average order value

**Products:**
- Best-selling products today (top 5)
- Products with zero sales today
- Stock changes (units sold per product)
- New low-stock alerts generated

**Customers:**
- New customers today
- Returning customers
- Customer inquiries received
- Inquiries resolved
- Average response time

### 2. Generate Report

**Format:**
```markdown
# Daily Report — {date}

## Revenue Summary
| Metric | Today | Yesterday | Change |
|--------|-------|-----------|--------|
| Revenue | ₹X | ₹Y | +/-Z% |
| Orders | N | N | +/-Z% |
| Avg Order Value | ₹X | ₹Y | +/-Z% |

## Top Sellers
1. {product} — {qty} sold — ₹{revenue}
2. ...

## Alerts
- {any inventory alerts}
- {any pending escalations}

## Tasks Summary
| Status | Count |
|--------|-------|
| Completed | N |
| Pending | N |
| Escalated | N |
```

### 3. Save and Log
- Save to `Plans/DAILY-REPORT_{YYYY-MM-DD}.md`
- Add summary entry to `Logs/LOG_{YYYY-MM-DD}.md`
- Update Dashboard.md metrics

## Output

- Daily report in `Plans/`
- Dashboard.md updated
- Log entry created
