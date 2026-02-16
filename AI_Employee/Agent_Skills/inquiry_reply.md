# Skill: Inquiry Reply

> **Skill ID:** inquiry-reply
> **Trigger:** Customer inquiry via `/trigger/inquiry`
> **Priority:** Medium
> **SLA:** Reply within 4 hours (business hours)

---

## Purpose

Draft professional, on-brand replies to customer inquiries following the Reply Plan framework.

## Input

Task file from `Needs_Action/` with prefix `INQUIRY_`

## Steps

### 1. Analyze Inquiry
- Identify the inquiry category:
  - **Product Question** — availability, material, sizing, care
  - **Order Status** — tracking, delivery timeline, confirmation
  - **Return/Exchange** — process, eligibility, timeline
  - **Complaint** — quality issue, wrong item, delayed delivery
  - **General** — partnership, bulk order, feedback
- Extract key details: customer name, email, related order/product

### 2. Gather Context
- If order-related: Pull order status, items, dates
- If product-related: Pull product details, stock, alternatives
- Check `Memory/Clients/` for customer history

### 3. Draft Reply

**Follow the 4-Step Framework:**

1. **Acknowledge** — Greet by first name, thank them for reaching out
2. **Address** — Directly answer their specific question
3. **Resolve** — Provide clear solution with specific timelines
4. **Follow-up** — Offer additional help, close warmly

**Tone Checklist:**
- [ ] Uses customer's first name
- [ ] Warm and professional tone
- [ ] Specific timelines (not "soon" or "shortly")
- [ ] Active voice throughout
- [ ] Under 150 words for simple queries, under 250 for complex
- [ ] Matches brand voice from Company Handbook

### 4. Check Escalation Rules
- Does this need human intervention? (See Company Handbook Section 6)
- If yes: Create escalation file instead of reply

### 5. Move to Approval
- Move completed draft to `Pending_Approval/`
- Include original inquiry + drafted reply in the same file

## Reply Templates

### Product Availability
```
Hi {name},

Great taste! The {product_name} is one of our favorites too.

{in_stock: "It's currently in stock and ready to ship!"}
{low_stock: "We only have {stock} left — I'd recommend ordering soon!"}
{out_of_stock: "This piece is temporarily out of stock. I expect it back by {date}. Want me to notify you?"}

You can view it here: {product_url}

Happy shopping!
{agent_name}, Royal Sparkle
```

### Order Status
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

### Return Request
```
Hi {name},

I'm sorry to hear that! We want you to be completely happy with your Royal Sparkle pieces.

Here's how the return process works:
1. I'll email you a return shipping label
2. Pack the item in its original packaging
3. Drop it off at any courier partner location
4. Once we receive it, your refund will process within 5-7 business days

Would you like me to start this process?

{agent_name}, Royal Sparkle
```

## Error Handling

| Situation | Action |
|-----------|--------|
| Angry customer | Use de-escalation template, check escalation rules |
| Unclear inquiry | Draft clarification question, not a full reply |
| Multiple issues in one email | Address each point separately, numbered |
| Request beyond AI authority | Escalate with recommendation |

## Output

- Reply draft in `Pending_Approval/`
- Customer memory update in `Memory/Clients/`
- Log entry created
