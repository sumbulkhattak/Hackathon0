# Watcher: New Order

> **Watcher ID:** new-order
> **Type:** Real-time
> **Trigger:** Order creation via API
> **Endpoint:** `POST /trigger/order`
> **Status:** ACTIVE

---

## Configuration

| Setting | Value |
|---------|-------|
| Monitor | All new orders |
| Auto-trigger | Immediately on order creation |
| Task Prefix | `ORDER-` |
| Destination | `Needs_Action/` |

## Behavior

1. Order placed via `POST /api/orders`
2. Backend fires `/trigger/order` with the new order ID
3. Task file created in `Needs_Action/`
4. `order-processing` skill picks up the task

## Validation Checks

- Order has at least 1 item
- All items have valid product IDs
- Total amount is greater than 0
- Customer email is provided

## Log Format

```
[{timestamp}] WATCHER:new-order | Order #{id} | Customer: {name} | Total: ₹{total} | Items: {count}
```
