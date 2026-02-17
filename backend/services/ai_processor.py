"""AI Processor Service — Claude API integration for task processing."""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

import config
from models import Order, Product, OrderItem
from services import vault, audit

logger = logging.getLogger(__name__)

# Escalation keywords (from Config/escalation_rules.md)
ESCALATION_KEYWORDS = {
    "angry": "TONE",
    "threatening": "TONE",
    "furious": "TONE",
    "disgusting": "TONE",
    "terrible": "TONE",
    "worst": "TONE",
    "lawyer": "LEGAL",
    "legal": "LEGAL",
    "court": "LEGAL",
    "consumer forum": "LEGAL",
    "sue": "LEGAL",
    "allergy": "SAFETY",
    "allergic": "SAFETY",
    "injury": "SAFETY",
    "rash": "SAFETY",
    "hurt": "SAFETY",
    "burn": "SAFETY",
}


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Call the Claude API and return the response text."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"[AI] Claude API call failed: {e}")
        raise


def _build_system_prompt(task_type: str) -> str:
    """Build system prompt from Company_Handbook + matching Agent_Skills file."""
    handbook = vault.read_company_handbook()

    skill_map = {
        "ORDER": "order_processing.md",
        "INQUIRY": "inquiry_reply.md",
        "INVENTORY-ALERT": "inventory_monitor.md",
        "PRODUCT-ADD": "update_product_listing.md",
        "PRICE-UPDATE": "update_product_listing.md",
    }
    skill_file = skill_map.get(task_type, "")
    skill_content = vault.read_agent_skill(skill_file) if skill_file else ""

    return f"""You are the Royal Sparkle AI Employee — an intelligent assistant for a premium artificial jewellery brand.

Your job is to process tasks following the company handbook and your assigned skill instructions.

=== COMPANY HANDBOOK ===
{handbook}

=== SKILL INSTRUCTIONS ===
{skill_content}

RULES:
- Follow the brand voice exactly: warm, elegant, feminine, premium
- Use the customer's first name
- Be specific about timelines (never say "soon" or "shortly")
- Keep replies concise: under 150 words for simple queries, under 250 for complex
- If unsure, recommend escalation rather than guessing
- Output your work as Markdown sections that can be appended to the task file
"""


def _detect_task_type(filename: str) -> str:
    """Detect task type from filename prefix."""
    if filename.startswith("ORDER-"):
        return "ORDER"
    elif filename.startswith("INQUIRY_"):
        return "INQUIRY"
    elif filename.startswith("INVENTORY-ALERT"):
        return "INVENTORY-ALERT"
    elif filename.startswith("ESCALATION-"):
        return "ESCALATION"
    elif filename.startswith("PRODUCT-ADD"):
        return "PRODUCT-ADD"
    elif filename.startswith("PRICE-UPDATE"):
        return "PRICE-UPDATE"
    return "UNKNOWN"


def _check_escalation(content: str) -> Optional[str]:
    """Check if content contains escalation trigger keywords. Returns type or None."""
    content_lower = content.lower()
    for keyword, esc_type in ESCALATION_KEYWORDS.items():
        if keyword in content_lower:
            return esc_type
    return None


def _slugify(name: str) -> str:
    """Convert a name to a filename-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')


def _update_client_memory(
    name: str,
    email: str,
    interaction_type: str,
    summary: str,
) -> None:
    """Create or update a client profile in Memory/Clients/."""
    slug = _slugify(name)
    filename = f"{slug}.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        existing = vault.read_memory_file("Clients", filename)
        # Append new interaction to existing profile
        new_entry = f"\n| {now} | {interaction_type} | {summary} |"
        updated = existing.rstrip() + new_entry + "\n"
        vault.write_memory_file("Clients", filename, updated)
    except FileNotFoundError:
        # Create new profile
        content = f"""# Client Profile: {name}

> **Created:** {now}
> **Last Contact:** {now}

## Contact
- **Name:** {name}
- **Email:** {email}

## Tags
- New Customer

## Interaction History

| Date | Type | Summary |
|------|------|---------|
| {now} | {interaction_type} | {summary} |
"""
        vault.write_memory_file("Clients", filename, content)


# ── Main processor ────────────────────────────────────────────────────────────

def process_task(filename: str, db: Session) -> dict:
    """Detect task type and route to the correct processor."""
    task_type = _detect_task_type(filename)
    start_time = time.time()

    try:
        if task_type == "ORDER":
            result = process_order_task(filename, db)
        elif task_type == "INQUIRY":
            result = process_inquiry_task(filename, db)
        elif task_type == "INVENTORY-ALERT":
            result = process_inventory_task(filename, db)
        elif task_type == "ESCALATION":
            result = process_escalation_task(filename, db)
        elif task_type == "PRODUCT-ADD":
            result = process_product_task(filename, db)
        elif task_type == "PRICE-UPDATE":
            result = process_price_update_task(filename, db)
        else:
            raise ValueError(f"Unknown task type: {task_type} (file: {filename})")

        duration = int((time.time() - start_time) * 1000)
        result["duration_ms"] = duration
        return result

    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        audit.write_audit_entry(
            source=f"ai-processor/{task_type.lower()}",
            action="task.process_failed",
            entity_type=task_type.lower(),
            entity_id=filename,
            status="ERROR",
            duration_ms=duration,
            error=str(e),
        )
        audit.append_daily_log(
            source=f"ai-processor/{task_type.lower()}",
            action="Process Failed",
            details=f"{filename} — {str(e)[:100]}",
            status="ERROR",
        )
        raise


# ── Order Processor ──────────────────────────────────────────────────────────

def process_order_task(filename: str, db: Session) -> dict:
    """Process an ORDER task: draft confirmation email + processing notes."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    # Extract order ID from filename: ORDER-{id}_{timestamp}.md
    order_id_match = re.search(r'ORDER-(\d+)', filename)
    order_id = int(order_id_match.group(1)) if order_id_match else None

    order = None
    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()

    system_prompt = _build_system_prompt("ORDER")
    user_prompt = f"""Process this order task. Generate:
1. A confirmation email draft following the template in your skill instructions
2. Processing notes (payment verification status, stock check, any flags)
3. A packing list

Here is the task file content:

{content}
"""
    if order:
        user_prompt += f"\nOrder status in database: {order.status}"
        user_prompt += f"\nCustomer: {order.customer_name} ({order.email})"

    ai_response = _call_claude(system_prompt, user_prompt)

    # Append AI output to the task file
    updated_content = content + f"""

---

## AI Processing Output

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    # Update client memory
    customer_name = metadata.get("Customer", "Unknown")
    email = metadata.get("Email", "")
    if customer_name and customer_name != "Unknown":
        _update_client_memory(
            customer_name, email, "Order",
            f"Order #{order_id} processed — {metadata.get('Total', 'N/A')}",
        )

    # Audit
    audit.write_audit_entry(
        source="ai-processor/order",
        action="task.processed",
        entity_type="order",
        entity_id=filename,
        details={"order_id": order_id, "customer": customer_name},
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/order",
        action="Task Processed",
        details=f"{filename} — Order #{order_id} by {customer_name}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "ORDER",
        "filename": filename,
        "moved_to": "Pending_Approval",
        "order_id": order_id,
    }


# ── Inquiry Processor ────────────────────────────────────────────────────────

def process_inquiry_task(filename: str, db: Session) -> dict:
    """Process an INQUIRY task: check escalation, then draft reply."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    # Check escalation triggers
    escalation_type = _check_escalation(content)
    if escalation_type:
        return _create_escalation(filename, content, metadata, escalation_type)

    system_prompt = _build_system_prompt("INQUIRY")
    user_prompt = f"""Draft a reply to this customer inquiry following the 4-step framework:
1. Acknowledge — Greet by first name, thank them
2. Address — Directly answer their question
3. Resolve — Provide clear solution with timelines
4. Follow-up — Offer help, close warmly

Also provide a tone checklist assessment.

Here is the task file:

{content}
"""

    ai_response = _call_claude(system_prompt, user_prompt)

    # Append AI output to the task file
    updated_content = content + f"""

---

## AI Drafted Reply

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    # Update client memory
    customer_name = metadata.get("Customer", "Unknown")
    email = metadata.get("Email", "")
    subject = metadata.get("Subject", "General inquiry")
    if customer_name and customer_name != "Unknown":
        _update_client_memory(
            customer_name, email, "Inquiry",
            f"Inquiry: {subject} — AI reply drafted",
        )

    audit.write_audit_entry(
        source="ai-processor/inquiry",
        action="task.processed",
        entity_type="inquiry",
        entity_id=filename,
        details={"customer": customer_name, "subject": subject},
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/inquiry",
        action="Task Processed",
        details=f"{filename} — Inquiry from {customer_name}: {subject}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "INQUIRY",
        "filename": filename,
        "moved_to": "Pending_Approval",
    }


def _create_escalation(
    original_filename: str,
    content: str,
    metadata: dict,
    escalation_type: str,
) -> dict:
    """Create an escalation file instead of processing normally."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    esc_filename = f"ESCALATION-{escalation_type}_{timestamp}.md"

    urgency = "URGENT" if escalation_type in ("LEGAL", "SAFETY") else "HIGH"
    customer_name = metadata.get("Customer", "Unknown")
    email = metadata.get("Email", "")

    esc_content = f"""# Escalation: {escalation_type}

> **Urgency:** {urgency}
> **Created:** {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
> **Source:** ai-processor/inquiry

## Customer
- **Name:** {customer_name}
- **Email:** {email}

## Context

This inquiry was auto-escalated because it matched escalation trigger: **{escalation_type}**

## Original Task

{content}

## AI Recommendation

This task requires human review due to {escalation_type.lower()} escalation triggers. Please review the original inquiry and respond directly.

## Required Action

- [ ] Review the original inquiry
- [ ] Determine appropriate response
- [ ] Respond to customer
- [ ] Log resolution
"""

    vault.write_task_file("Needs_Action", esc_filename, esc_content)

    # Move original to Pending_Approval with escalation note
    updated_content = content + f"""

---

## ESCALATED

**Escalation Type:** {escalation_type}
**Urgency:** {urgency}
**Escalation File:** {esc_filename}
**Reason:** Matched auto-escalation trigger

## Status: ESCALATED
"""
    vault.write_task_file("Needs_Action", original_filename, updated_content)
    vault.move_task_file(original_filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/inquiry",
        action="task.escalated",
        entity_type="escalation",
        entity_id=esc_filename,
        details={
            "original_file": original_filename,
            "escalation_type": escalation_type,
            "urgency": urgency,
            "customer": customer_name,
        },
        queue="Needs_Action",
        status="ESCALATED",
    )
    audit.append_daily_log(
        source="ai-processor/inquiry",
        action="Task Escalated",
        details=f"{original_filename} → {esc_filename} ({escalation_type})",
        status="ESCALATED",
    )

    return {
        "status": "escalated",
        "task_type": "INQUIRY",
        "filename": original_filename,
        "escalation_file": esc_filename,
        "escalation_type": escalation_type,
        "urgency": urgency,
        "moved_to": "Pending_Approval",
    }


# ── Inventory Processor ──────────────────────────────────────────────────────

def process_inventory_task(filename: str, db: Session) -> dict:
    """Process an INVENTORY-ALERT task: cross-reference DB stock, generate restock plan."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    # Get current stock from DB
    low_stock_products = db.query(Product).filter(Product.stock < 10).all()
    stock_info = ""
    for p in low_stock_products:
        urgency = "OUT OF STOCK" if p.stock == 0 else (
            "CRITICAL" if p.stock <= 3 else (
                "LOW" if p.stock <= 7 else "WARNING"
            )
        )
        stock_info += f"- {p.name} (ID: {p.id}): {p.stock} units — {urgency}\n"

    system_prompt = _build_system_prompt("INVENTORY-ALERT")
    user_prompt = f"""Analyze this inventory alert and generate:
1. A prioritized restock plan with recommended quantities
2. A supplier email draft
3. Website action recommendations

Current stock levels from database:
{stock_info if stock_info else "No products below threshold currently."}

Task file:
{content}
"""

    ai_response = _call_claude(system_prompt, user_prompt)

    updated_content = content + f"""

---

## AI Restock Analysis

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)

    # Determine destination based on severity
    critical_count = int(metadata.get("Critical Items", "0"))
    if critical_count > 0:
        dest_queue = "Pending_Approval"
    else:
        # Check if priority is WARNING-level only
        priority = metadata.get("Priority", "High")
        dest_queue = "Plans" if priority == "Warning" else "Pending_Approval"

    vault.move_task_file(filename, "Needs_Action", dest_queue)

    audit.write_audit_entry(
        source="ai-processor/inventory",
        action="task.processed",
        entity_type="inventory",
        entity_id=filename,
        details={
            "products_affected": metadata.get("Products Affected", "0"),
            "critical_items": critical_count,
        },
        queue=dest_queue,
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/inventory",
        action="Task Processed",
        details=f"{filename} — {metadata.get('Products Affected', '?')} products, {critical_count} critical",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "INVENTORY-ALERT",
        "filename": filename,
        "moved_to": dest_queue,
        "critical_count": critical_count,
    }


# ── Escalation Processor ─────────────────────────────────────────────────────

def process_escalation_task(filename: str, db: Session) -> dict:
    """Move escalation to Pending_Approval with human-review flag. No AI processing."""
    content = vault.read_task_file("Needs_Action", filename)

    updated_content = content + f"""

---

## Status: AWAITING HUMAN REVIEW

**Flagged:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

> This escalation requires direct human attention. No AI processing was performed.
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/escalation",
        action="task.escalation_forwarded",
        entity_type="escalation",
        entity_id=filename,
        queue="Pending_Approval",
        status="AWAITING_REVIEW",
    )
    audit.append_daily_log(
        source="ai-processor/escalation",
        action="Escalation Forwarded",
        details=f"{filename} → Pending_Approval (human review required)",
        status="AWAITING_REVIEW",
    )

    return {
        "status": "forwarded",
        "task_type": "ESCALATION",
        "filename": filename,
        "moved_to": "Pending_Approval",
        "note": "No AI processing — requires human review",
    }


# ── Product Add Processor ──────────────────────────────────────────────────

def process_product_task(filename: str, db: Session) -> dict:
    """Process a PRODUCT-ADD task: validate details and draft listing plan."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    system_prompt = _build_system_prompt("PRODUCT-ADD")
    user_prompt = f"""Review this product addition request. Generate:
1. Validation check (name, description, pricing against handbook rules)
2. SEO-friendly product listing draft
3. Category verification
4. Any concerns or flags

Here is the task file:

{content}
"""

    ai_response = _call_claude(system_prompt, user_prompt)

    # Build queued action args
    price_str = metadata.get("Price", "0").replace("\u20b9", "").replace(",", "").strip()
    try:
        price_val = float(price_str)
    except ValueError:
        price_val = 0

    updated_content = content + f"""

---

## AI Processing Output

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | create_product | {{"name": "{metadata.get('Product Name', '')}", "description": "{metadata.get('Description', '')}", "price": {price_val}, "category_id": {metadata.get('Category ID', '1')}, "stock": {metadata.get('Stock', '50')}}} | PENDING |

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/product",
        action="task.processed",
        entity_type="product",
        entity_id=filename,
        details={"product_name": metadata.get("Product Name", "")},
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/product",
        action="Task Processed",
        details=f"{filename} — Product: {metadata.get('Product Name', 'Unknown')}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "PRODUCT-ADD",
        "filename": filename,
        "moved_to": "Pending_Approval",
    }


# ── Price Update Processor ─────────────────────────────────────────────────

def process_price_update_task(filename: str, db: Session) -> dict:
    """Process a PRICE-UPDATE task: validate against margin rules."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    product_id = metadata.get("Product ID", "")
    product = None
    if product_id.isdigit():
        product = db.query(Product).filter(Product.id == int(product_id)).first()

    system_prompt = _build_system_prompt("PRICE-UPDATE")
    user_prompt = f"""Review this pricing change request. Validate:
1. New price vs handbook margin rules (minimum 30% margin)
2. Comparison with current pricing tier
3. Impact assessment
4. Any flags or concerns

Here is the task file:

{content}
"""
    if product:
        user_prompt += f"\nCurrent DB price: \u20b9{product.price:,.0f}, Stock: {product.stock}"

    ai_response = _call_claude(system_prompt, user_prompt)

    new_price_str = metadata.get("New Price", "0").replace("\u20b9", "").replace(",", "").strip()
    try:
        new_price_val = float(new_price_str)
    except ValueError:
        new_price_val = 0

    updated_content = content + f"""

---

## AI Processing Output

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | update_price | {{"id": {product_id}, "new_price": {new_price_val}, "reason": "{metadata.get('Reason', '')}"}} | PENDING |

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/price-update",
        action="task.processed",
        entity_type="product",
        entity_id=filename,
        details={"product_id": product_id, "product_name": metadata.get("Product Name", ""), "new_price": new_price_str},
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/price-update",
        action="Task Processed",
        details=f"{filename} — {metadata.get('Product Name', 'Unknown')}: \u20b9{metadata.get('Current Price', '?')} \u2192 \u20b9{metadata.get('New Price', '?')}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "PRICE-UPDATE",
        "filename": filename,
        "moved_to": "Pending_Approval",
    }
