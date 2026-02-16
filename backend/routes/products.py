import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Category, Product
from schemas import CategoryResponse, ProductCreate, ProductUpdate

router = APIRouter(prefix="/api", tags=["Products"])


def product_to_response(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "image_url": product.image_url,
        "images": product.images_list,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else "",
        "stock": product.stock,
        "featured": product.featured,
        "created_at": product.created_at,
    }


# ─── Categories ─────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


# ─── Products ───────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if category:
        query = query.join(Category).filter(Category.slug == category)
    if featured is not None:
        query = query.filter(Product.featured == featured)
    products = query.all()
    return [product_to_response(p) for p in products]


@router.get("/products/{slug}")
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_response(product)


@router.post("/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    data = product.model_dump()
    data["images"] = json.dumps(data.get("images", []))
    db_product = Product(**data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return product_to_response(db_product)


@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product.model_dump(exclude_unset=True)
    if "images" in update_data:
        update_data["images"] = json.dumps(update_data["images"])
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return product_to_response(db_product)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
