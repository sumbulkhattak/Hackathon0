# Skill: Order Processing

> **Skill ID:** order-processing
> **Trigger:** New order placed via `/trigger/order`
> **Priority:** High
> **SLA:** Process within 24 hours

---

## Purpose

Automatically handle incoming orders from placement through dispatch preparation.

## Input

Task file from `Needs_Action/` with prefix `ORDER-`

## Steps

### 1. Verify Payment
- Check order total against payment confirmation
- If payment pending → flag for manual review
- If payment confirmed → proceed

### 2. Validate Order
- Confirm all items are in stock (real-time check)
- Verify shipping address is complete and valid
- Check for duplicate orders (same customer, same items, within 1 hour)

### 3. Send Confirmation Email
**Template:**
```
Subject: Your Royal Sparkle Order #{order_id} is Confirmed!

Hi {first_name},

Thank you for your beautiful order! Here's what we're preparing for you:

{item_list}

Order Total: {total}
Estimated Delivery: {delivery_date}

We'll send you a tracking number once your order ships.

With sparkle,
The Royal Sparkle Team
```

### 4. Prepare Packing List
- Generate item list with quantities
- Note any special packaging requirements
- Flag fragile items (chandelier earrings, hair pin sets)

### 5. Update Order Status
- Move status from `pending` → `confirmed`
- Log action in `Logs/`

### 6. Move Task File
- Move completed task from `Needs_Action/` → `Pending_Approval/`
- Add processing notes to the file

## Error Handling

| Error | Action |
|-------|--------|
| Item out of stock after order | Escalate immediately, contact customer |
| Invalid address | Move to Pending_Approval with note for human review |
| Suspected duplicate order | Hold and flag for human decision |
| Payment mismatch | Escalate to finance |

## Output

- Updated task file in `Pending_Approval/`
- Confirmation email draft (pending approval)
- Packing list generated
- Log entry created
