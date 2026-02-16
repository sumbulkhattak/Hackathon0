# Skill: Update Jewellery Product Listing

> **Skill ID:** update-product-listing
> **Trigger:** Inventory change / New product / Manual request / Seasonal campaign
> **Priority:** Medium
> **SLA:** Draft within 1 hour; publish after manager approval (within 24 hours)

---

## Purpose

Create, update, or deactivate product listings on the Royal Sparkle e-commerce platform. Ensures all listings follow brand guidelines, contain accurate details, and maintain SEO standards. All listing changes require manager approval before going live.

## Inputs

| Input | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `action` | enum | Yes | Calling skill / task | One of: `create`, `update`, `deactivate`, `reactivate`, `seasonal_update` |
| `product_id` | integer | Yes (except `create`) | DB | Existing product identifier |
| `product_name` | string | Yes | Task file / DB | Display name for the product |
| `category` | enum | Yes | Task file | One of: `necklaces`, `earrings`, `bracelets`, `rings`, `anklets`, `hair_accessories` |
| `subcategory` | string | No | Task file | E.g., `studs`, `pendants`, `chokers`, `charm_bracelets` |
| `price` | float | Yes | DB / task file | Retail price in ₹ |
| `compare_at_price` | float | No | Task file | Original price for sale display (strike-through) |
| `description` | string | Yes | Task file / AI-generated | Product description (brand voice) |
| `materials` | list | Yes | Task file | Materials used (from Section 10 approved list) |
| `images` | list | Yes | Task file / Incoming_Files/ | Product image file paths (min 3, max 8) |
| `stock_quantity` | integer | Yes | DB | Current inventory count |
| `weight` | string | No | Task file | Product weight (e.g., "15g") |
| `dimensions` | string | No | Task file | Product dimensions if applicable |
| `care_instructions` | string | No | Default from Handbook | Care instructions (default: Section 10 standard) |
| `tags` | list | No | AI-generated | SEO tags and search keywords |
| `collection` | string | No | Task file | Collection name (e.g., "Diwali 2026", "Everyday Elegance") |
| `is_featured` | boolean | No | Task file | Whether to feature on homepage |

## Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `listing_draft` | Markdown | `Pending_Approval/LISTING-{slug}_{timestamp}.md` | Full listing content for review |
| `listing_status` | enum | Audit log | `drafted`, `approved`, `published`, `deactivated`, `rejected` |
| `product_update` | object | DB via MCP | Updated product record in e-commerce platform |
| `audit_entry` | JSONL | `Logs/audit/AUDIT_{date}.jsonl` | Structured audit record |
| `seo_metadata` | object | MCP Catalog | Title tag, meta description, Open Graph tags |
| `image_urls` | list | MCP Catalog | Processed and optimized image URLs |

## Approval Requirements

| Action | Approval Required | Authority | Handbook Reference |
|--------|-------------------|-----------|-------------------|
| Create new listing | **Yes — manager** | Manager → Publish | Section 9: Product Listing Change |
| Update description / images | **Yes — manager** | Manager → Publish | Section 9: Product Listing Change |
| Update stock quantity (restock) | No — auto-update | AI Agent (Tier 1) | Section 11: Update Inventory Count |
| Price change | **Yes — manager** | Manager → Apply | Section 9: AI Must NEVER #4 |
| Deactivate (out of stock) | No — auto-deactivate | AI Agent (Tier 1) | Section 10 / Inventory Skill |
| Reactivate (back in stock) | **Yes — manager** | Manager → Publish | Section 9: Product Listing Change |
| Seasonal / sale pricing | **Yes — manager** | Manager → Apply | Section 7: Pricing Rules |
| Featured placement | **Yes — manager** | Manager → Approve | Section 9: Product Listing Change |

### Approval Pipeline

```
AI drafts listing → Pending_Approval/LISTING-{slug}_{timestamp}.md
    → Manager reviews content, images, pricing, SEO
    → Approved → MCP Catalog Server publishes → Approved/
    → Rejected → Rejected/ (with revision notes for AI to re-draft)
```

**Auto-update exceptions** (no approval needed):
- Stock quantity adjustments (restock only — never reduce without approval)
- Mark as "Out of Stock" when quantity hits 0
- Show "Low Stock" badge when quantity is 1–3

## Steps

### 1. Validate Product Data
- Verify all required fields are present
- Check `category` is valid (Section 10: Categories)
- Verify `materials` against approved materials list (Section 10: Materials)
- Validate `price` is within tier range (Section 7: Price Ranges)
- Ensure minimum 3 product images exist

### 2. Generate / Update Description
- Write in Royal Sparkle brand voice (Section 3)
- Structure:
  - **Opening line:** Evocative, aspirational (1 sentence)
  - **Feature highlights:** 3–5 bullet points (materials, design, occasion)
  - **Styling suggestion:** 1 sentence on how to wear/pair it
  - **Care note:** Standard from Handbook Section 10
- Word count: 80–150 words
- Avoid: superlatives ("best ever"), unverifiable claims, competitor mentions

### 3. Optimize Images
- Call MCP to process images:
  - Resize to standard dimensions (800×800 primary, 400×400 thumbnails)
  - Apply consistent white/beige background
  - Ensure minimum 3 angles: front, detail close-up, lifestyle/on-model
- Generate alt text for accessibility and SEO

### 4. Generate SEO Metadata
- **Title tag:** `{Product Name} | {Category} | Royal Sparkle` (max 60 chars)
- **Meta description:** 1-sentence summary with key feature + CTA (max 155 chars)
- **URL slug:** lowercase, hyphenated product name
- **Tags:** category, material, occasion, collection, style keywords
- **Open Graph:** title, description, primary image URL

### 5. Build Listing Draft
- Combine all elements into structured Markdown for review
- Include pricing with tier classification
- Include stock status and availability
- Include all images with captions

### 6. Route for Approval
- Stock-only updates → auto-apply via MCP (Step 7)
- All other changes → write to `Pending_Approval/` and STOP
- Include before/after comparison for updates

### 7. Publish via MCP Catalog Server
- Call `mcp__catalog__create_product` or `mcp__catalog__update_product`
- Upload processed images via `mcp__catalog__upload_image`
- Set SEO metadata via `mcp__catalog__set_seo`
- Verify published listing matches draft

### 8. Post-Publish Actions
- Write audit entry to `Logs/audit/`
- Update product record in `Memory/Finance/` if price changed
- Move task file to `Approved/`
- Refresh Dashboard.md
- If featured: verify homepage placement

## MCP Integration

### MCP Server: `mcp__catalog`

The Update Product Listing skill integrates with an MCP-compliant e-commerce catalog server for product management.

#### Tools

| MCP Tool | Purpose | Parameters |
|----------|---------|------------|
| `mcp__catalog__create_product` | Create a new product listing | `product_data`, `images`, `seo`, `publish` |
| `mcp__catalog__update_product` | Update an existing listing | `product_id`, `fields_to_update` |
| `mcp__catalog__get_product` | Retrieve current listing data | `product_id` |
| `mcp__catalog__upload_image` | Upload and process product image | `product_id`, `image_path`, `position`, `alt_text` |
| `mcp__catalog__set_seo` | Set SEO metadata for a product | `product_id`, `title_tag`, `meta_description`, `og_tags`, `tags` |
| `mcp__catalog__set_stock` | Update stock quantity | `product_id`, `quantity`, `action` (`set`, `increment`, `decrement`) |
| `mcp__catalog__deactivate` | Deactivate a listing (hide from store) | `product_id`, `reason` |
| `mcp__catalog__reactivate` | Reactivate a previously hidden listing | `product_id` |
| `mcp__catalog__set_featured` | Set or remove homepage featured status | `product_id`, `featured`, `position` |
| `mcp__catalog__bulk_update` | Batch update multiple products | `updates[]` (array of product updates) |

#### Configuration

```json
{
  "mcpServers": {
    "catalog": {
      "type": "e-commerce",
      "platform": "royal-sparkle-store",
      "base_url": "https://api.royalsparkle.in/catalog",
      "image_config": {
        "max_images_per_product": 8,
        "min_images_per_product": 3,
        "primary_size": "800x800",
        "thumbnail_size": "400x400",
        "accepted_formats": ["jpg", "png", "webp"],
        "max_file_size_mb": 5,
        "background": "white"
      },
      "seo_config": {
        "title_max_length": 60,
        "description_max_length": 155,
        "auto_generate_slug": true
      },
      "stock_config": {
        "low_stock_threshold": 3,
        "out_of_stock_auto_deactivate": true,
        "restock_auto_reactivate": false
      }
    }
  }
}
```

#### Error Handling

| MCP Error | Action |
|-----------|--------|
| `product_not_found` | Log error, verify product_id, flag for human review |
| `image_upload_failed` | Retry once; if persistent, proceed without that image and flag |
| `invalid_price` | Reject update, log error, alert manager |
| `duplicate_slug` | Append sequential number to slug, retry |
| `rate_limited` | Queue update, retry after cooldown |
| `publish_failed` | Log error, keep draft in Pending_Approval for retry |
| `image_too_large` | Auto-compress; if still too large, flag for manual resize |

#### Security Rules
- **Never** modify prices without manager approval (Section 9, Rule #4)
- **Never** publish a listing without minimum 3 images
- **Never** use customer photos as product images without consent
- All listing changes are logged in audit with before/after snapshots
- Image uploads are scanned for malicious content

## Product Description Template

```markdown
## {Product Name}

{Evocative opening line — aspirational, elegant, 1 sentence}

**Highlights:**
- {Material and finish}
- {Design feature — pattern, stones, motif}
- {Occasion — everyday, festive, bridal, gifting}
- {Comfort — lightweight, adjustable, hypoallergenic}

**Styling Tip:** {1 sentence on pairing or wearing suggestion}

**Care:** {Standard care from Handbook Section 10}

**Materials:** {comma-separated list}
**Weight:** {weight}
```

## Error Handling

| Situation | Action |
|-----------|--------|
| Product not found in DB | Log error, skip update, alert human |
| Insufficient images (< 3) | Reject listing, create task to gather more images |
| Price outside tier range | Flag anomaly for manager review |
| Description fails brand voice check | Re-generate with stricter prompt; escalate if 2nd attempt fails |
| Category not recognized | Map to nearest valid category, flag for human confirmation |
| Duplicate product detected | Alert human — potential data quality issue |

## Rules

- Follow Company Handbook Section 2 (Visual Identity) for all images and branding
- Follow Section 3 (Brand Voice) for all product descriptions
- Follow Section 7 (Pricing) for price tier compliance
- Follow Section 9 (Sensitive Actions) — never modify prices without approval
- Follow Section 10 (Product Knowledge) for accurate materials and care info
- All listings must have: name, description, ≥ 3 images, price, materials, care, category
- Never publish a product with 0 stock — deactivate until restocked
- Seasonal pricing only during pre-approved campaign periods (Section 7)
- Use consistent photography style across all listings (Section 2)
