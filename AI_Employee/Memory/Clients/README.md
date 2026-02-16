# Client Memory

Store customer profiles and interaction history here.

## File Format

One file per customer: `{customer_name_slug}.md`

### Template

```markdown
# Customer: {Full Name}

## Contact
- **Email:** {email}
- **Phone:** {phone}
- **City:** {city}

## Order History
| Order ID | Date | Total | Status |
|----------|------|-------|--------|
| #{id} | {date} | ₹{total} | {status} |

## Preferences
- Favorite categories: {list}
- Preferred price range: {range}
- Communication preference: {email/phone/whatsapp}

## Interaction Notes
- {date}: {brief note about interaction}

## Tags
{vip / returning / new / high-value / complaint-history}
```

## Rules
- Update after every order and inquiry
- Never store payment/card details
- Flag VIP customers (3+ orders or ₹5,000+ lifetime spend)
