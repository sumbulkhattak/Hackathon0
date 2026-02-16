# Skill: Respond to Customer Inquiry

> **Skill ID:** respond-to-inquiry
> **Trigger:** Customer inquiry via `/trigger/inquiry`, email webhook, or social media
> **Priority:** Medium–High (depends on inquiry type and escalation triggers)
> **SLA:** Draft reply within 4 hours (business hours); resolution within 24 hours

---

## Purpose

Analyze incoming customer inquiries, gather relevant context, draft a professional on-brand reply following the 4-Step Framework, and route through the approval pipeline. Handles the full lifecycle from intake to resolution tracking.

## Inputs

| Input | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `inquiry_id` | string | Yes | Task filename | Task identifier (e.g., `INQUIRY_2026-02-16_14-30-00`) |
| `customer_name` | string | Yes | Task file | Customer's full name |
| `customer_email` | string | Yes | Task file | Customer's email address |
| `subject` | string | Yes | Task file | Inquiry subject line |
| `message` | string | Yes | Task file | Full inquiry message body |
| `channel` | enum | No | Task file / trigger | `email`, `website_form`, `social_media`, `phone_callback` (default: `email`) |
| `related_order_id` | integer | No | Task file / detected | Associated order number (if mentioned) |
| `related_product` | string | No | Task file / detected | Referenced product name or SKU |
| `attachments` | list | No | Task file | Customer-uploaded files (photos, screenshots) |
| `priority_override` | enum | No | Calling skill | Force priority: `low`, `medium`, `high`, `urgent` |
| `is_followup` | boolean | No | Task file | Whether this is a follow-up to a previous inquiry |
| `previous_thread_id` | string | No | Memory/Clients/ | Previous inquiry reference for thread continuity |

## Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `reply_draft` | Markdown | `Pending_Approval/REPLY-{slug}_{timestamp}.md` | Drafted reply for human review |
| `inquiry_classification` | object | Audit log | `{category, priority, sentiment, escalation_needed}` |
| `escalation_file` | Markdown | `Needs_Action/ESCALATION-{type}_{timestamp}.md` | Created if escalation triggers match |
| `client_memory_update` | Markdown | `Memory/Clients/{slug}.md` | Updated customer profile with interaction |
| `audit_entry` | JSONL | `Logs/audit/AUDIT_{date}.jsonl` | Structured audit record |
| `reply_email` | Triggered | Via Send Email skill | Email sent after approval |
| `follow_up_task` | Markdown | `Needs_Action/FOLLOW-UP_{timestamp}.md` | Scheduled 24-hour follow-up check |

## Approval Requirements

| Inquiry Type | Approval Required | Authority | Handbook Reference |
|--------------|-------------------|-----------|-------------------|
| Product availability / info | Yes — human review | AI drafts → Pending_Approval | Section 4: Tier 2 |
| Order status inquiry | Yes — human review | AI drafts → Pending_Approval | Section 4: Tier 2 |
| Simple FAQ (care, shipping) | Yes — human review | AI drafts → Pending_Approval | Section 4: Tier 2 |
| Return/exchange request | Yes — human review | AI drafts → Pending_Approval | Section 6: Refund Policy |
| Complaint | Yes — human review | AI drafts → supervisor reviews | Section 4: Tier 2 |
| Complaint with angry language | **Auto-escalate** | Human only (Tier 3) | Section 9: Escalation Triggers |
| Legal mention | **Auto-escalate URGENT** | Management (Tier 3) | Section 9: Escalation Triggers |
| Safety concern | **Auto-escalate URGENT** | Management (Tier 3) | Section 13: Product Safety |
| Bulk / custom order inquiry | **Escalate** | Sales manager (Tier 3) | Section 9: Bulk Order Pricing |
| Refund request ≥ ₹2,000 | **Escalate** | Manager (Tier 3) | Section 6: Refund ≥ ₹2,000 |

### Approval Pipeline

```
AI classifies + drafts → Pending_Approval/REPLY-{slug}_{timestamp}.md
    → Human reviews tone, accuracy, completeness
    → Approved → Send Email skill dispatches → Approved/
    → Rejected → Rejected/ (AI re-drafts with feedback)

Escalation path (parallel):
    → ESCALATION-{type}_{timestamp}.md → Needs_Action/ → Tier 3 human
```

## Steps

### 1. Intake & Classification
- Read inquiry from `Needs_Action/INQUIRY_{timestamp}.md`
- Classify the inquiry into one of:
  - **Product Question** — availability, material, sizing, care, pricing
  - **Order Status** — tracking, delivery timeline, confirmation
  - **Return/Exchange** — process, eligibility, timeline
  - **Complaint** — quality issue, wrong item, delayed delivery, poor experience
  - **General** — partnership, bulk order, feedback, compliment
  - **Refund Request** — money back request with amount
- Detect sentiment: `positive`, `neutral`, `concerned`, `frustrated`, `angry`
- Assign priority based on Section 4 SLAs:
  - Complaint → High (1-hour response SLA)
  - Order issue → High (2-hour response SLA)
  - Return/refund → Medium-High (2-hour response SLA)
  - General inquiry → Medium (4-hour response SLA)

### 2. Escalation Check
Run against all escalation triggers (Section 9):

| Check | Trigger Keywords / Conditions | Action |
|-------|-------------------------------|--------|
| Angry language | "unacceptable", "worst", "disgusted", "never again", "terrible" | `ESCALATION-TONE` |
| Legal threat | "lawyer", "court", "consumer forum", "legal action", "sue" | `ESCALATION-LEGAL` (URGENT) |
| Safety concern | "allergy", "rash", "broke", "injury", "bleeding", "allergic" | `ESCALATION-SAFETY` (URGENT) |
| High-value refund | Refund amount ≥ ₹2,000 | `ESCALATION-REFUND` |
| Repeat complaint | Same customer, 3+ complaints in Memory/Clients/ | `ESCALATION-REPEAT` |
| Social media (high reach) | 1000+ followers mentioned or public complaint | `ESCALATION-SOCIAL` |
| Bulk order | "bulk", "wholesale", "corporate", "100+", "custom order" | `ESCALATION-BULK` |

If any trigger matches:
- Create escalation file in `Needs_Action/` with full context
- Continue drafting AI reply as recommendation (marked as "AI Recommendation — Pending Human Decision")
- Do NOT move inquiry to Pending_Approval — leave for human

### 3. Gather Context
- **Customer history:** Load from `Memory/Clients/{slug}.md`
  - Previous orders, complaints, preferences, VIP status
  - If 3+ orders OR ₹5,000+ lifetime spend → flag as VIP (Section 4, Rule 6)
- **Order data:** If `related_order_id` exists, pull order details from DB
  - Current status, tracking number, delivery estimate, items
- **Product data:** If `related_product` mentioned, pull from DB
  - Stock status, price, materials, care instructions
- **Thread history:** If `is_followup`, load previous interaction from Memory

### 4. Draft Reply
Follow the **4-Step Framework** (Section 8):

**Step 1: Acknowledge**
- Use customer's first name
- Thank them for reaching out
- Acknowledge their specific situation with empathy

**Step 2: Address**
- Directly answer their question or describe the issue
- Reference specific order/product details
- Be factual and precise — no vague language

**Step 3: Resolve**
- Provide a clear solution with exact timelines and dates
- Include specific next steps (numbered if multiple)
- Reference relevant policies (return window, delivery estimates)

**Step 4: Follow-up**
- Offer additional help
- Close warmly with brand-appropriate sign-off
- Include agent name + "Royal Sparkle"

**Quality Checks:**
- [ ] Uses customer's first name (not "Dear Customer")
- [ ] Active voice throughout (not "Your order has been...")
- [ ] Specific dates/timelines (not "soon" or "shortly")
- [ ] Under word limit: 100–150 simple, 200–250 complex
- [ ] No unfilled placeholders
- [ ] Matches brand voice (Section 3): warm, confident, empathetic
- [ ] No internal system references (queues, AI processing, vault)
- [ ] Single clear next step for the customer

### 5. Build Reply File
- Write reply draft to `Pending_Approval/REPLY-{slug}_{timestamp}.md`
- Include sections:
  - Original inquiry (full text)
  - AI classification (category, priority, sentiment)
  - Context gathered (order status, customer history summary)
  - Drafted reply
  - Escalation notes (if any triggers matched)
  - Approval metadata

### 6. Update Client Memory
- Append interaction to `Memory/Clients/{slug}.md`:
  - Date, inquiry type, subject, summary, status
  - Update interaction count
  - Flag as VIP if threshold reached
- If new customer: create client file

### 7. Schedule Follow-Up
- Create follow-up task for 24 hours post-resolution (Section 4, Rule 5)
- Follow-up template: "Hi {name}, just checking in — is everything sparkling with your order?"
- Skip follow-up for: compliments, general info requests, bulk inquiries

### 8. Post-Draft Actions
- Write audit entry to `Logs/audit/`
- Append to daily log in `Logs/LOG_{date}.md`
- Refresh Dashboard.md

## MCP Integration

### MCP Server: `mcp__knowledge`

The Respond to Inquiry skill integrates with an MCP-compliant knowledge base for FAQ resolution and context enrichment.

#### Tools

| MCP Tool | Purpose | Parameters |
|----------|---------|------------|
| `mcp__knowledge__search_faq` | Search FAQ database for matching answers | `query`, `category`, `max_results` |
| `mcp__knowledge__get_product_info` | Get detailed product information | `product_id` or `product_name` |
| `mcp__knowledge__get_order_status` | Get real-time order status and tracking | `order_id` |
| `mcp__knowledge__get_shipping_estimate` | Get delivery estimate by location | `pincode`, `shipping_method` |
| `mcp__knowledge__search_policies` | Search Company Handbook for relevant policies | `query`, `section` |
| `mcp__knowledge__get_customer_history` | Retrieve customer interaction history | `customer_email` or `customer_name` |
| `mcp__knowledge__classify_intent` | AI-powered intent classification | `message`, `subject` |
| `mcp__knowledge__detect_sentiment` | Detect customer sentiment from message | `message` |

### MCP Server: `mcp__email` (shared with Send Email skill)

| MCP Tool | Purpose | Parameters |
|----------|---------|------------|
| `mcp__email__send` | Send approved reply | `to`, `subject`, `body_html`, `body_text`, `from_name`, `reply_to` |
| `mcp__email__get_thread` | Retrieve email thread for context | `thread_id` |

#### Configuration

```json
{
  "mcpServers": {
    "knowledge": {
      "type": "knowledge-base",
      "faq_source": "AI_Employee/Company_Handbook.md",
      "product_source": "database",
      "order_source": "database",
      "client_memory": "AI_Employee/Memory/Clients/",
      "classification": {
        "categories": ["product_question", "order_status", "return_exchange", "complaint", "general", "refund_request"],
        "sentiment_levels": ["positive", "neutral", "concerned", "frustrated", "angry"],
        "confidence_threshold": 0.7
      },
      "escalation": {
        "tone_keywords": ["unacceptable", "worst", "disgusted", "never again", "terrible", "horrible", "scam", "fraud", "cheat"],
        "legal_keywords": ["lawyer", "court", "consumer forum", "legal action", "sue", "advocate", "police"],
        "safety_keywords": ["allergy", "rash", "broke", "injury", "bleeding", "allergic", "reaction", "burn", "skin"],
        "bulk_keywords": ["bulk", "wholesale", "corporate", "custom order", "100+", "50+", "large quantity"]
      }
    }
  }
}
```

#### Error Handling

| MCP Error | Action |
|-----------|--------|
| `faq_no_match` | Proceed with handbook-based reasoning; flag for human review |
| `order_not_found` | Ask customer to verify order number in reply draft |
| `product_not_found` | Draft reply acknowledging and requesting clarification |
| `classification_low_confidence` | Default to "General" category, flag for human classification |
| `sentiment_detection_failed` | Default to "neutral", proceed normally |
| `customer_history_unavailable` | Proceed without history; note in reply context |
| `knowledge_base_timeout` | Retry once; proceed with handbook-only context if timeout persists |

#### Security Rules
- **Never** return customer data from one customer's inquiry to another
- **Never** expose internal order processing details to customers
- **Never** share PII in audit logs (log inquiry subject + classification only, not message body)
- Customer attachments are scanned before processing
- Escalation files include full context but are internal-only (never sent to customer)

## Reply File Format

```markdown
# Reply: {Subject} — {Customer Name}

> **Reply ID:** REPLY-{slug}_{timestamp}
> **Source Inquiry:** {inquiry_filename}
> **Created:** {YYYY-MM-DD HH:MM:SS UTC}
> **Priority:** {priority}
> **Classification:** {category} | Sentiment: {sentiment}

---

## Original Inquiry

**From:** {customer_name} ({customer_email})
**Subject:** {subject}
**Received:** {inquiry_date}

{full_message_body}

---

## Context Gathered

| Field | Value |
|-------|-------|
| **Customer Status** | {new / returning / VIP} |
| **Previous Interactions** | {count} |
| **Related Order** | #{order_id} — {order_status} |
| **Related Product** | {product_name} — {stock_status} |
| **Escalation Triggers** | {none / list of matched triggers} |

---

## Drafted Reply

```email
Subject: Re: {original_subject}

{4-step-framework reply content}

{agent_name}, Royal Sparkle
```

---

## Approval Notes

- **Reviewer:** {assigned_reviewer or "Any supervisor"}
- **Approval SLA:** {based on inquiry priority}
- **Escalation flags:** {if any}
- **AI Confidence:** {high / medium / low}

---

> Auto-generated by Royal Sparkle AI Employee — Respond to Inquiry Skill
```

## Error Handling

| Situation | Action |
|-----------|--------|
| Empty or malformed inquiry | Log warning, create clarification task |
| Customer not found in Memory | Create new client profile, proceed without history |
| Multiple issues in one inquiry | Address each point separately (numbered), note in reply |
| Inquiry in non-English language | Detect language, escalate to human with translation note |
| Ambiguous intent | Draft clarification question instead of full reply |
| Duplicate inquiry (same customer, same subject, < 1 hour) | Link to existing reply, do not create duplicate |
| SLA breach imminent | Auto-escalate priority, alert supervisor |

## Rules

- Follow Company Handbook Section 3 (Brand Voice) for all reply content
- Follow Section 4 (Customer Support Rules) for SLAs and tier routing
- Follow Section 8 (Email Response Guidelines) for the 4-Step Framework
- Follow Section 9 (Sensitive Action Rules) for escalation triggers
- Never share internal processes with customers (queue names, AI processing, vault structure)
- Never blame the customer, even for user error (Section 4, Rule 2)
- Always confirm understanding before providing solutions (Section 4, Rule 4)
- One issue per thread — acknowledge all, resolve sequentially (Section 4, Rule 1)
- Schedule 24-hour follow-up after resolution (Section 4, Rule 5)
- Flag VIP customers: 3+ orders OR ₹5,000+ lifetime spend (Section 4, Rule 6)
