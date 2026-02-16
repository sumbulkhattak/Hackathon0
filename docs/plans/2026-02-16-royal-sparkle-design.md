# Royal Sparkle — E-Commerce Design Document

**Date:** 2026-02-16
**Status:** Approved
**Type:** Full-stack e-commerce application

## Overview

Premium artificial jewellery e-commerce website with a feminine luxury aesthetic. Built for hackathon demo with mock checkout.

## Architecture

Monorepo with two applications:
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Framer Motion → `localhost:3000`
- **Backend**: FastAPI + SQLite → `localhost:8000`

## Brand Identity

- **Colors**: Blush pink (#F9E4E4), Rose gold (#B76E79), White, Soft beige (#F5F0EB)
- **Fonts**: Playfair Display (headings), Lato (body)
- **Style**: Rounded cards (16px), soft shadows, elegant animations

## Data Model

- **categories**: id, name, slug
- **products**: id, name, slug, description, price, image_url, category_id (FK), stock, featured, created_at
- **orders**: id, customer_name, email, phone, address, city, total, status, created_at
- **order_items**: id, order_id (FK), product_id (FK), quantity, price

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Hero banner, featured products, categories |
| `/shop` | Product grid with category filters |
| `/product/[slug]` | Product detail + add to cart |
| `/cart` | Cart management |
| `/checkout` | Mock checkout form |
| `/admin` | Orders, products CRUD, stats |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/products` | List products |
| GET | `/api/products/{slug}` | Single product |
| POST | `/api/products` | Admin: create |
| PUT | `/api/products/{id}` | Admin: update |
| DELETE | `/api/products/{id}` | Admin: delete |
| GET | `/api/categories` | List categories |
| POST | `/api/orders` | Place order |
| GET | `/api/orders` | Admin: list orders |
| PATCH | `/api/orders/{id}` | Update order status |
| GET | `/api/stats` | Dashboard stats |
| POST | `/api/hooks/order-trigger` | AI hook |
| POST | `/api/hooks/inquiry` | AI hook |
| POST | `/api/hooks/inventory-alert` | AI hook |

## Cart

Client-side React Context with localStorage persistence. No server-side cart.

## Excluded (YAGNI)

- User auth/registration
- Real payment processing
- Image upload
- Search beyond category filter
- Reviews/ratings
