# Skill: Generate Invoice

> **Skill ID:** generate-invoice
> **Trigger:** Order confirmed / Refund processed / Manual request
> **Priority:** High
> **SLA:** Generate within 30 minutes of order confirmation

---

## Purpose

Generate professional, branded PDF invoices for Royal Sparkle orders, refunds, and credit notes. Invoices follow Indian GST compliance rules and Royal Sparkle visual identity.

## Inputs

| Input | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `order_id` | integer | Yes | Task file / DB | Order identifier |
| `invoice_type` | enum | Yes | Calling skill | One of: `sale`, `refund`, `credit_note`, `proforma` |
| `customer_name` | string | Yes | Task file / DB | Full customer name for billing |
| `customer_email` | string | Yes | Task file / DB | Customer email for delivery |
| `billing_address` | object | Yes | DB | Street, city, state, PIN code |
| `shipping_address` | object | Yes | DB | Street, city, state, PIN code (can match billing) |
| `line_items` | list | Yes | DB | Array of: `{product_name, sku, quantity, unit_price, discount, tax_rate, total}` |
| `order_total` | float | Yes | DB | Gross order total (₹) |
| `discount_amount` | float | No | DB | Total discount applied (₹) |
| `tax_breakdown` | object | Yes | Calculated | `{cgst, sgst, igst}` — based on shipping state |
| `payment_method` | string | Yes | DB | Payment method used (UPI, Card, NetBanking, COD) |
| `payment_status` | enum | Yes | DB | `paid`, `pending`, `refunded`, `partial_refund` |
| `coupon_code` | string | No | DB | Coupon applied (if any) |
| `notes` | string | No | Calling skill | Special instructions or gift messages |

## Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `invoice_pdf` | PDF file | `AI_Employee/Invoices/INV-{order_id}_{timestamp}.pdf` | Branded PDF invoice |
| `invoice_markdown` | Markdown | `Plans/INVOICE-{order_id}_{timestamp}.md` | Plain-text version for vault reference |
| `invoice_number` | string | Audit log | Unique invoice number: `RS-INV-{YYYY}-{sequential}` |
| `audit_entry` | JSONL | `Logs/audit/AUDIT_{date}.jsonl` | Structured audit record |
| `finance_update` | Markdown | `Memory/Finance/invoices-{YYYY-MM}.md` | Monthly invoice register entry |

## Approval Requirements

| Invoice Type | Approval Required | Authority | Handbook Reference |
|--------------|-------------------|-----------|-------------------|
| Standard sale invoice | No — auto-generate | AI Agent (Tier 1) | Section 5: Order Processing |
| Proforma invoice | No — auto-generate | AI Agent (Tier 1) | Section 11: Decision Authority |
| Refund credit note ≤ ₹500 | No — auto-generate | AI Agent (Tier 1) | Section 6: Refund ≤ ₹500 |
| Refund credit note ₹500–₹1,999 | Yes — supervisor | AI drafts → Pending_Approval | Section 6: Refund ₹500–₹1,999 |
| Refund credit note ₹2,000–₹4,999 | Yes — manager | AI drafts → Pending_Approval | Section 6: Refund ₹2,000–₹4,999 |
| Refund credit note ≥ ₹5,000 | Yes — director | Auto-escalate URGENT | Section 6: Refund ≥ ₹5,000 |
| Custom/bulk order invoice | Yes — manager | Sales manager → Finance | Section 9: Bulk Order Pricing |

### Approval Pipeline

```
AI generates invoice → Pending_Approval/INVOICE-{order_id}_{timestamp}.md
    → Human reviews amounts, line items, tax calculations
    → Approved → MCP Invoice Server generates PDF → Approved/
    → Rejected → Rejected/ (with correction notes)
```

## Steps

### 1. Validate Order Data
- Verify `order_id` exists in the database
- Confirm all line items match order records
- Validate `order_total` = sum of (line item totals) − `discount_amount` + tax
- Verify billing/shipping addresses are complete (street, city, state, PIN)
- Check for duplicate invoice (same order_id + invoice_type)

### 2. Calculate Tax
- Determine tax type based on seller vs. buyer state:
  - **Same state** → CGST (9%) + SGST (9%)
  - **Different state** → IGST (18%)
- Apply tax per line item based on product category
- Round to 2 decimal places

### 3. Generate Invoice Number
- Format: `RS-INV-{YYYY}-{5-digit-sequential}`
- Example: `RS-INV-2026-00142`
- For refunds: `RS-CN-{YYYY}-{5-digit-sequential}` (Credit Note)
- Sequential counter stored in `Memory/Finance/invoice-counter.md`

### 4. Build Invoice Content
- Apply Royal Sparkle branding (Section 2: Visual Identity)
- Include all mandatory fields:
  - Company name, GSTIN, address
  - Invoice number, date, due date
  - Customer billing and shipping address
  - Line items with HSN codes, quantities, rates, tax, totals
  - Tax summary (CGST/SGST or IGST)
  - Grand total in words and figures
  - Payment status and method
  - Terms and conditions

### 5. Route for Approval (if required)
- Standard sales: skip to Step 6
- Refund/credit notes above threshold: write to `Pending_Approval/` and STOP
- Attach tax calculation breakdown for reviewer

### 6. Generate PDF via MCP
- Call `mcp__invoice__generate_pdf` with invoice data
- Save PDF to `AI_Employee/Invoices/`
- Save Markdown copy to `Plans/` for vault reference

### 7. Deliver Invoice
- Attach PDF to order confirmation email (via Send Email skill)
- Or send standalone invoice email if generated post-order

### 8. Post-Generation Actions
- Write audit entry to `Logs/audit/`
- Update monthly invoice register in `Memory/Finance/invoices-{YYYY-MM}.md`
- Update invoice counter in `Memory/Finance/invoice-counter.md`
- Refresh Dashboard.md

## MCP Integration

### MCP Server: `mcp__invoice`

The Generate Invoice skill integrates with an MCP-compliant document generation server for PDF creation.

#### Tools

| MCP Tool | Purpose | Parameters |
|----------|---------|------------|
| `mcp__invoice__generate_pdf` | Generate a branded PDF invoice | `invoice_data`, `template_id`, `branding` |
| `mcp__invoice__generate_credit_note` | Generate a credit note PDF | `credit_note_data`, `original_invoice_ref` |
| `mcp__invoice__get_next_number` | Get next sequential invoice number | `type` (`invoice` or `credit_note`), `year` |
| `mcp__invoice__validate_gstin` | Validate a GSTIN number | `gstin` |
| `mcp__invoice__get_hsn_code` | Look up HSN code for a product category | `category`, `subcategory` |

#### Configuration

```json
{
  "mcpServers": {
    "invoice": {
      "type": "document-generator",
      "template_dir": "AI_Employee/Templates/invoices/",
      "output_dir": "AI_Employee/Invoices/",
      "branding": {
        "company_name": "Royal Sparkle",
        "gstin": "XXXXXXXXXXXXXXXXX",
        "address": "Mumbai, Maharashtra, India",
        "logo_path": "AI_Employee/Templates/assets/logo.png",
        "primary_color": "#B76E79",
        "font_heading": "Playfair Display",
        "font_body": "Poppins"
      },
      "tax_config": {
        "default_rate": 18,
        "cgst_rate": 9,
        "sgst_rate": 9,
        "igst_rate": 18,
        "seller_state": "Maharashtra"
      },
      "format": "PDF",
      "page_size": "A4"
    }
  }
}
```

#### Error Handling

| MCP Error | Action |
|-----------|--------|
| `pdf_generation_failed` | Retry once; fall back to Markdown-only invoice |
| `invalid_tax_data` | Log error, flag for human review before generating |
| `template_not_found` | Use default template, log warning |
| `duplicate_invoice_number` | Increment counter, retry generation |
| `storage_full` | Alert tech team, queue invoice for later generation |
| `hsn_lookup_failed` | Use generic HSN code, flag for manual correction |

#### Security Rules
- **Never** include customer payment card details on invoices
- **Never** modify historical invoices — issue credit notes for corrections
- Invoice PDFs are immutable once generated; corrections require new documents
- All invoice generation is logged in audit with full line-item detail
- GSTIN and tax calculations must comply with Indian GST rules

## Invoice Template Structure

```
┌─────────────────────────────────────────────┐
│  [Royal Sparkle Logo]                       │
│  Royal Sparkle — Shine Like Royalty         │
│  GSTIN: XXXXXXXXXXXXXXXXX                   │
│  Mumbai, Maharashtra, India                 │
├─────────────────────────────────────────────┤
│  INVOICE / CREDIT NOTE                      │
│  Invoice No: RS-INV-2026-00142             │
│  Date: 16 Feb 2026                          │
│  Due Date: 16 Feb 2026 (Prepaid)           │
├──────────────────┬──────────────────────────┤
│  Bill To:        │  Ship To:               │
│  {customer}      │  {customer}             │
│  {address}       │  {address}              │
├──────────────────┴──────────────────────────┤
│  # │ Item      │ HSN  │ Qty │ Rate │ Total │
│  1 │ ...       │ ...  │ ... │  ... │  ...  │
│  2 │ ...       │ ...  │ ... │  ... │  ...  │
├─────────────────────────────────────────────┤
│  Subtotal:                          ₹X,XXX │
│  Discount ({code}):                 -₹XXX  │
│  CGST (9%):                          ₹XXX  │
│  SGST (9%):                          ₹XXX  │
│  ─────────────────────────────────────────  │
│  GRAND TOTAL:                       ₹X,XXX │
│  (Rupees {amount_in_words} Only)            │
├─────────────────────────────────────────────┤
│  Payment: {method} | Status: {status}       │
│  Terms: No cash refunds. Returns within 7d. │
│  Thank you for shopping with Royal Sparkle! │
└─────────────────────────────────────────────┘
```

## Error Handling

| Situation | Action |
|-----------|--------|
| Order not found in database | Log error, skip generation, alert human |
| Tax calculation mismatch | Flag for human review; do not auto-generate |
| Missing customer address | Create follow-up task to collect address |
| Duplicate invoice request | Return existing invoice reference, do not regenerate |
| PDF generation fails | Fall back to Markdown invoice, flag for PDF retry |

## Rules

- Follow Company Handbook Section 2 (Visual Identity) for all branding
- Follow Section 5 (Order Processing) for order lifecycle alignment
- Follow Section 6 (Refund Policy) for credit note thresholds
- Invoice numbers must be sequential with no gaps
- All amounts in INR (₹) with 2 decimal places
- Tax calculations must comply with Indian GST regulations
- Historical invoices are immutable — use credit notes for corrections
- Store both PDF and Markdown versions for redundancy
