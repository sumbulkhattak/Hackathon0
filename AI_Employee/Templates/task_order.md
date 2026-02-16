# Order: #{order_id}

> **Priority:** HIGH
> **Created:** {YYYY-MM-DD HH:MM:SS}
> **Source:** watcher/new-order
> **Skill:** order-processing
> **SLA:** Process within 24 hours

---

## Customer
- **Name:** {customer_name}
- **Email:** {customer_email}
- **Phone:** {customer_phone}
- **City:** {customer_city}

## Order Details

| Item | SKU | Qty | Unit Price | Subtotal |
|------|-----|-----|-----------|----------|
| {product_name} | {sku} | {qty} | {price} | {subtotal} |

- **Subtotal:** {subtotal}
- **Shipping:** {shipping}
- **Discount:** {discount}
- **Total:** {total}

## Payment
- **Method:** {payment_method}
- **Status:** {payment_status}
- **Transaction ID:** {transaction_id}

## Shipping
- **Address:** {full_address}
- **Method:** {shipping_method}
- **Estimated Delivery:** {delivery_date}

## Processing Notes
{AI adds notes here during processing}

## Status
- [ ] Payment verified
- [ ] Items in stock confirmed
- [ ] Confirmation email drafted
- [ ] Packing list generated
- [ ] Moved to Pending_Approval
