# Royal Sparkle — Premium Artificial Jewellery E-Commerce

A full-stack e-commerce website for artificial jewellery with a feminine luxury aesthetic.

**Tech Stack:** Next.js + Tailwind CSS + Framer Motion | FastAPI + SQLite

---

## Folder Structure

```
royal-sparkle/
│
├── frontend/                     # Next.js Frontend
│   ├── src/app/                  # Pages (App Router)
│   │   ├── page.tsx              #   Homepage
│   │   ├── layout.tsx            #   Root layout
│   │   ├── globals.css           #   Tailwind + brand theme
│   │   ├── shop/page.tsx         #   Product listing
│   │   ├── product/[slug]/       #   Product detail
│   │   ├── cart/page.tsx         #   Shopping cart
│   │   ├── checkout/page.tsx     #   Mock checkout
│   │   └── admin/page.tsx        #   Admin dashboard
│   ├── src/components/           # Reusable Components
│   │   ├── Navbar.tsx            #   Navigation bar
│   │   ├── Footer.tsx            #   Site footer
│   │   ├── ProductCard.tsx       #   Product card
│   │   └── CartProvider.tsx      #   Cart context + state
│   ├── src/lib/                  # Utilities
│   │   ├── api.ts                #   API client functions
│   │   └── types.ts              #   TypeScript interfaces
│   ├── styles/                   # Design Tokens
│   │   └── theme.ts              #   Colors, fonts, shadows
│   └── public/                   # Static assets
│
├── backend/                      # FastAPI Backend
│   ├── main.py                   # App entry + router registration
│   ├── models.py                 # SQLAlchemy database models
│   ├── database.py               # SQLite + SQLAlchemy engine
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── seed.py                   # Sample product data (12 items)
│   ├── requirements.txt          # Python dependencies
│   └── routes/                   # API Route Modules
│       ├── products.py           #   Products + categories CRUD
│       ├── orders.py             #   Orders + stats endpoints
│       └── hooks.py              #   AI integration hook endpoints
│
├── ai-hooks/                     # AI Integration Scripts
│   ├── __init__.py               # Package exports
│   ├── order_trigger.py          # Order placed trigger
│   ├── inquiry_trigger.py        # Customer inquiry trigger
│   └── inventory_alert.py        # Low stock alert trigger
│
└── docs/plans/                   # Design documents
```

---

## Setup Instructions

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API runs at `http://localhost:8000`. The database is auto-created and seeded on first launch.

API docs available at `http://localhost:8000/docs` (Swagger UI).

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend runs at `http://localhost:3000`.

---

## Features

| Feature | Description |
|---------|-------------|
| Homepage | Hero banner, featured products, category grid, brand story |
| Product Listing | Category filters, sort options, responsive grid |
| Product Detail | Full product info, quantity picker, add to cart |
| Cart System | Client-side cart with localStorage, quantity management |
| Checkout | Mock checkout form with order confirmation |
| Order Database | SQLite storage for orders with status tracking |
| Admin Dashboard | Stats overview, order management, product list |

## AI Integration Hooks

| Endpoint | Script | Purpose |
|----------|--------|---------|
| `POST /api/hooks/order-trigger` | `ai-hooks/order_trigger.py` | Triggered when a new order is placed |
| `POST /api/hooks/inquiry` | `ai-hooks/inquiry_trigger.py` | Customer inquiry webhook |
| `POST /api/hooks/inventory-alert` | `ai-hooks/inventory_alert.py` | Low stock alert (auto when stock < 10) |

**Payload format:**
```json
{
  "event": "new_order",
  "data": { "order_id": 1, "total": 1299.0 }
}
```

**Usage from Python:**
```python
from ai_hooks import trigger_order_hook, trigger_inquiry_hook, trigger_inventory_alert

trigger_order_hook(order_id=1, customer_name="Priya", email="priya@example.com", total=1299.0, items_count=2)
```

## Design System

- **Colors:** Blush pink (#F9E4E4), Rose gold (#B76E79), White, Soft beige (#F5F0EB)
- **Fonts:** Playfair Display (headings), Lato (body)
- **Style:** Rounded cards (16px), soft shadows, Framer Motion animations
