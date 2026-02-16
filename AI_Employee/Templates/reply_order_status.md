## Reply Template: Order Status

**Use when:** Customer asks about order tracking, delivery timeline, or confirmation.

---

```
Hi {name},

Here's the latest on your order #{order_id}:

Status: {status}
{if_shipped: "Tracking: {tracking_number}"}
{if_shipped: "Expected delivery: {delivery_date}"}
{if_pending: "We're processing it now — you'll receive a confirmation shortly."}

Let me know if you need anything else!

{agent_name}, Royal Sparkle
```
