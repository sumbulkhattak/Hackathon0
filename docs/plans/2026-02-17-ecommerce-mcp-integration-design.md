# E-Commerce MCP Integration — Design Document

**Date:** 2026-02-17
**Status:** Approved
**Approach:** MCP-First (Approach A)
**Autonomy:** Gate everything — human decides via dashboard

---

## 1. Overview

Integrate the AI Employee with the Royal Sparkle e-commerce website (Next.js + FastAPI) using 3 local MCP servers. The AI Employee gains 4 capabilities: add products, update pricing, monitor orders, and respond to customers. All write actions go through the existing HITL approval pipeline. Claude calls MCP tools during task processing, and the executor runs approved actions via the same MCP servers.

**Platform:** Existing Next.js + FastAPI site in this repo
**MCP Transport:** Local Python servers (stdio), same repo, same deployment
**Orchestration:** Ralph Wiggum Loop handles all scheduling

---

## 2. Architecture

```
Customer Action → Webhook/Trigger → Needs_Action/
  → Ralph Loop Phase 1 → Claude + MCP tools → Pending_Approval/
  → Human approves → Phase 3 → MCP executes → Archived/
```

### Three MCP Servers

```
backend/mcp/
├── __init__.py           # Registry: get_all_tools(), get_server(), call_tool()
├── catalog_server.py     # mcp__catalog — product & pricing
├── knowledge_server.py   # mcp__knowledge — orders & customer intelligence
└── email_server.py       # mcp__email — customer communication
```

### Key Decisions

- 3 MCP servers built as Python modules using the `mcp` Python SDK (stdio transport)
- Claude calls MCP tools during Phase 1 (scan & process)
- Phase 3 (execute) also uses MCP tools for approved write actions
- All writes go through HITL — Claude drafts, human approves, executor runs MCP tools
- Reads are free — monitoring orders, checking stock, searching FAQs happen during Phase 1

---

## 3. MCP Server Definitions

### Server 1: `mcp__catalog` — Product & Pricing Management

| Tool | Args | Returns | Write? |
|------|------|---------|--------|
| `get_product` | `slug` or `id` | Full product details | No |
| `list_products` | `category?`, `featured?`, `low_stock?` | Filtered product array | No |
| `create_product` | `name`, `description`, `price`, `category_id`, `stock`, `images`, `featured` | Created product ID | Yes |
| `update_product` | `id`, fields to update | Updated product | Yes |
| `update_price` | `id`, `new_price`, `reason` | Old/new price confirmation | Yes |
| `set_stock` | `id`, `quantity`, `reason` | Old/new stock confirmation | Yes |
| `delete_product` | `id` | Confirmation | Yes |

All tools use existing SQLAlchemy `Product` model directly.

### Server 2: `mcp__knowledge` — Order Monitoring & Customer Intelligence

| Tool | Args | Returns | Write? |
|------|------|---------|--------|
| `get_order` | `order_id` | Full order with items, status, customer | No |
| `list_orders` | `status?`, `customer_email?`, `date_from?`, `date_to?` | Filtered order list | No |
| `get_order_stats` | — | Today's totals: count, revenue, pending, completed | No |
| `get_customer_history` | `email` or `slug` | Client memory profile + order history | No |
| `search_faq` | `query` | Matching handbook sections + policies | No |
| `get_product_info` | `slug` | Product details for customer-facing responses | No |
| `search_policies` | `topic` | Relevant handbook sections | No |

Sources: SQLite DB for orders/products, vault Memory/Clients/ for profiles, Company_Handbook.md for FAQ/policies.

### Server 3: `mcp__email` — Customer Communication

| Tool | Args | Returns | Write? |
|------|------|---------|--------|
| `draft_reply` | `to`, `subject`, `body`, `template?` | Formatted email draft | Yes |
| `send_email` | `to`, `subject`, `body` | Send confirmation | Yes |
| `get_thread` | `customer_email` | Previous email history from vault | No |

`send_email` logs to audit trail (no real SMTP yet — can be wired up later). `draft_reply` formats using handbook templates.

---

## 4. Capability → Skill → MCP Mapping

### Capability 1: Add Products

**Skill:** `update_product_listing.md`
**Trigger:** `PRODUCT-ADD_*.md` in Needs_Action/, or POST `/trigger/product`
**MCP Tools Used:**
1. `mcp__catalog.get_product` — check for duplicates
2. `mcp__knowledge.search_policies` — pricing rules validation
3. `mcp__catalog.create_product` — executed on approval (Phase 3)

### Capability 2: Update Pricing

**Skill:** `update_product_listing.md` (pricing section)
**Trigger:** `PRICE-UPDATE_*.md` in Needs_Action/, or POST `/trigger/price-update`
**MCP Tools Used:**
1. `mcp__catalog.get_product` — current price lookup
2. `mcp__knowledge.search_policies` — margin/discount rules
3. `mcp__catalog.update_price` — executed on approval (Phase 3)

### Capability 3: Monitor Orders

**Skill:** `order_processing.md` + `daily_reporting.md`
**Trigger:** Automatic — Ralph Loop scans every cycle
**MCP Tools Used:**
1. `mcp__knowledge.get_order_stats` — dashboard metrics
2. `mcp__knowledge.list_orders(status="pending")` — stale order detection
3. `mcp__catalog.list_products(low_stock=True)` — inventory alerts

### Capability 4: Respond to Customers

**Skill:** `respond_to_inquiry.md` + `inquiry_reply.md`
**Trigger:** `INQUIRY_*.md` in Needs_Action/, or POST `/trigger/inquiry`
**MCP Tools Used:**
1. `mcp__knowledge.get_customer_history` — context
2. `mcp__knowledge.search_faq` — relevant answers
3. `mcp__knowledge.get_order_status` — if order-related
4. `mcp__email.draft_reply` — format response
5. `mcp__email.send_email` — executed on approval (Phase 3)

---

## 5. AI Processor + MCP Integration

### Tool Calling Flow

```
ai_processor.process_task(filename, db)
  ├── 1. Read task file content
  ├── 2. Detect task type (ORDER, INQUIRY, PRODUCT-ADD, PRICE-UPDATE, etc.)
  ├── 3. Load matching agent skill instructions
  ├── 4. Discover available MCP tools from all 3 servers
  │       └── catalog_server.list_tools()  → 7 tools
  │       └── knowledge_server.list_tools() → 7 tools
  │       └── email_server.list_tools()     → 3 tools
  ├── 5. Call Claude with system prompt + task content + 17 MCP tools
  ├── 6. Claude responds with tool_use blocks
  ├── 7. AI processor routes tool calls to the right MCP server
  ├── 8. Claude continues reasoning with tool results (loop)
  ├── 9. Claude produces final output:
  │       • Action plan
  │       • Queued write actions (not executed yet)
  │       • Risk assessment + confidence score
  └── 10. Append output to task file → move to Pending_Approval/
```

### Queued Actions Format (in task file)

```markdown
## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | create_product | {"name": "Kundan Choker", "price": 2499, ...} | PENDING |
| 2 | email | send_email | {"to": "priya@gmail.com", "subject": "...", ...} | PENDING |
```

### Phase 3 Execution

```python
def _run_action(task_type, content, filename):
    actions = parse_queued_actions(content)
    results = []
    for action in actions:
        server = get_mcp_server(action["server"])
        result = server.call_tool(action["tool"], action["args"])
        results.append({"tool": action["tool"], "result": result})
    return {"steps_completed": len(results), "results": results}
```

---

## 6. Frontend Changes

### New Dashboard Tab: "E-Commerce"

5th tab alongside Overview, Task Queue, Activity Log, Memory:

| Widget | Data Source | Purpose |
|--------|------------|---------|
| Product Stats | `mcp__catalog.list_products` | Total products, low stock, recently added |
| Order Monitor | `mcp__knowledge.get_order_stats` | Today's orders, revenue, pending/completed |
| Pending Responses | Task queue filter INQUIRY_* | Inquiries awaiting reply with SLA countdown |
| Recent Price Changes | Audit log filter price-update | Last 5 pricing changes with old/new values |

### New Trigger Buttons (Task Queue tab)

| Button | Action | Creates |
|--------|--------|---------|
| "+ Add Product" | Form → POST `/trigger/product` | `PRODUCT-ADD_*.md` |
| "+ Update Price" | Dropdown + price → POST `/trigger/price-update` | `PRICE-UPDATE_*.md` |
| "+ Customer Reply" | Email + message → POST `/trigger/inquiry` | `INQUIRY_*.md` |

### Task Queue Enhancements

- Task type badges: ORDER, INQUIRY, PRODUCT-ADD, PRICE-UPDATE, INVENTORY-ALERT (color-coded)
- Queued Actions preview for Pending_Approval tasks (shows MCP action table)
- Quick filters by task type

### New API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /trigger/product` | Create product addition task |
| `POST /trigger/price-update` | Create pricing update task |
| `GET /api/ecommerce/stats` | Aggregate product/order/inquiry stats |

---

## 7. Files

### New

| File | Purpose |
|------|---------|
| `backend/mcp/__init__.py` | MCP registry: get_all_tools(), get_server(), call_tool() |
| `backend/mcp/catalog_server.py` | Product & pricing MCP tools (7 tools) |
| `backend/mcp/knowledge_server.py` | Order & customer intelligence MCP tools (7 tools) |
| `backend/mcp/email_server.py` | Customer communication MCP tools (3 tools) |
| `backend/routes/ecommerce.py` | New trigger + stats endpoints |
| `backend/tests/test_mcp_catalog.py` | Catalog server tests |
| `backend/tests/test_mcp_knowledge.py` | Knowledge server tests |
| `backend/tests/test_mcp_email.py` | Email server tests |
| `backend/tests/test_ecommerce_routes.py` | Trigger/stats endpoint tests |

### Modified

| File | Change |
|------|--------|
| `backend/services/ai_processor.py` | MCP tool discovery + tool calling loop with Claude |
| `backend/services/task_executor.py` | Parse queued actions, execute via MCP servers |
| `backend/routes/triggers.py` | Add /trigger/product, /trigger/price-update |
| `backend/main.py` | Register new routes |
| `frontend/src/lib/ai-api.ts` | Add triggerProduct(), triggerPriceUpdate(), getEcommerceStats() |
| `frontend/src/app/ai-employee/page.tsx` | E-Commerce tab, trigger buttons, task type badges, queued actions preview |

---

## 8. Rules

1. **Never auto-execute writes** — all product/pricing/email actions require human approval
2. **Never bypass HITL** — MCP write tools only run in Phase 3 (after approval)
3. **Never expose internals** — customer-facing emails must not mention MCP, queues, or AI processing
4. **Reads are free** — order monitoring, FAQ search, product lookup happen without approval
5. **Audit everything** — every MCP tool call is logged to the audit trail
6. **Handbook compliance** — all pricing changes validated against margin rules (min 30%), discount limits
7. **Escalation preserved** — angry customers, legal mentions, safety issues still auto-escalate per handbook
