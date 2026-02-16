# Skill: Inventory Monitor

> **Skill ID:** inventory-monitor
> **Trigger:** `/trigger/inventory` or daily scheduled scan
> **Priority:** High (Critical items) / Medium (Low stock)
> **SLA:** Critical items escalated within 1 hour

---

## Purpose

Monitor product inventory levels, generate restock alerts, and create supplier communication drafts.

## Input

Task file from `Needs_Action/` with prefix `INVENTORY-ALERT_`

## Steps

### 1. Classify Urgency

| Stock Level | Urgency | Action Timeline |
|-------------|---------|-----------------|
| 0 units | OUT OF STOCK | Immediate — mark unavailable on site |
| 1-3 units | CRITICAL | Within 24 hours — emergency restock |
| 4-7 units | LOW | Within 3 days — standard restock |
| 8-threshold | WARNING | Within 1 week — plan restock |

### 2. Generate Restock Plan

For each affected product:
- Current stock level
- Average daily sales (from order history)
- Estimated days until stockout
- Recommended restock quantity (30-day supply)
- Preferred supplier (from Memory/Finance/)

### 3. Draft Supplier Communication

**Template:**
```
Subject: Restock Order — Royal Sparkle [{date}]

Dear Supplier,

We need to restock the following items:

{product_table}

Please confirm:
- Availability
- Unit pricing for the quantities above
- Estimated delivery timeline

Regards,
Royal Sparkle Procurement
```

### 4. Website Actions

| Stock Level | Website Action |
|-------------|---------------|
| 0 | Mark "Out of Stock" — disable add-to-cart |
| 1-3 | Show "Only {n} left!" badge |
| 4-7 | Show "Low Stock" indicator |
| 8+ | Normal display |

### 5. Move to Appropriate Queue
- **CRITICAL items (0-3):** → `Pending_Approval/` with URGENT flag
- **LOW items (4-7):** → `Pending_Approval/` for routine review
- **WARNING items (8+):** → `Plans/` as informational note

## Restock Quantity Formula

```
recommended_qty = (avg_daily_sales * 30) + safety_stock
safety_stock = avg_daily_sales * 7  (one week buffer)
```

If no sales data available, default to:
- High-demand (featured): 50 units
- Standard: 30 units
- Low-demand: 15 units

## Error Handling

| Situation | Action |
|-----------|--------|
| Product completely out of stock | URGENT escalation + hide from website |
| Supplier not responding | Flag for human follow-up after 24 hours |
| Bulk products low simultaneously | Prioritize by sales velocity |
| Seasonal spike detected | Adjust safety stock to 14-day buffer |

## Output

- Restock plan in `Pending_Approval/` or `Plans/`
- Supplier email draft
- Updated inventory notes in `Memory/Finance/`
- Log entry created
