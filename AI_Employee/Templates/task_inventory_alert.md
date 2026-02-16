# Inventory Alert: {date}

> **Priority:** {CRITICAL / HIGH / MEDIUM}
> **Created:** {YYYY-MM-DD HH:MM:SS}
> **Source:** watcher/low-stock OR schedule/morning-stock-scan
> **Skill:** inventory-monitor
> **SLA:** Critical within 1 hour, Low within 3 days

---

## Affected Products

| Product | SKU | Current Stock | Level | Avg Daily Sales | Days Until Stockout |
|---------|-----|--------------|-------|-----------------|---------------------|
| {name} | {sku} | {stock} | {CRITICAL/LOW/WARNING} | {avg} | {days} |

## Restock Recommendations

| Product | Recommended Qty | Supplier | Est. Cost |
|---------|----------------|----------|-----------|
| {name} | {qty} | {supplier} | {cost} |

## Supplier Communication Draft
```
{AI-generated supplier email}
```

## Website Actions Required

| Product | Action |
|---------|--------|
| {name} | {Mark "Out of Stock" / Show "Only N left!" / Show "Low Stock"} |

## Status
- [ ] Products classified by urgency
- [ ] Restock quantities calculated
- [ ] Supplier email drafted
- [ ] Website actions listed
- [ ] Moved to appropriate queue
