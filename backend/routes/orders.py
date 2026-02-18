import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Product, Order, OrderItem
from schemas import OrderCreate, OrderResponse, OrderStatusUpdate, DashboardStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Orders"])


@router.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total = 0.0
    order_items = []
    low_stock_products = []

    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}",
            )
        item_total = product.price * item.quantity
        total += item_total
        order_items.append(
            {"product_id": product.id, "quantity": item.quantity, "price": product.price}
        )
        product.stock -= item.quantity
        if product.stock < 10:
            low_stock_products.append(
                {"product_id": product.id, "name": product.name, "stock": product.stock}
            )

    db_order = Order(
        customer_name=order.customer_name,
        email=order.email,
        phone=order.phone,
        address=order.address,
        city=order.city,
        total=total,
    )
    db.add(db_order)
    db.flush()

    for item_data in order_items:
        db.add(OrderItem(order_id=db_order.id, **item_data))

    db.commit()
    db.refresh(db_order)

    # Log order trigger
    logger.info(f"[HOOK] Order trigger: Order #{db_order.id} placed, total Rs.{total}")

    # Log inventory alerts
    for lsp in low_stock_products:
        logger.info(
            f"[HOOK] Inventory alert: {lsp['name']} (ID: {lsp['product_id']}) low stock: {lsp['stock']} remaining"
        )

    return db_order


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}", response_model=OrderResponse)
def update_order_status(order_id: int, update: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = update.status
    db.commit()
    db.refresh(order)
    return order


# ─── Admin Stats ────────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0.0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    low_stock_count = db.query(func.count(Product.id)).filter(Product.stock < 10).scalar() or 0
    return DashboardStats(
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_products=total_products,
        low_stock_count=low_stock_count,
    )
