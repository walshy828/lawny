"""Product catalog API — browse and manage lawn care products."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from app.database import get_db
from app.models import ProductCatalog, PRODUCT_CATEGORIES

router = APIRouter(prefix="/api/products", tags=["products"])


def _prod_dict(p: ProductCatalog) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "npk_ratio": p.npk_ratio,
        "active_ingredient": p.active_ingredient,
        "application_rate_per_1k": p.application_rate_per_1k,
        "coverage_sqft_per_bag": p.coverage_sqft_per_bag,
        "bag_size": p.bag_size,
        "safe_grass_types": p.safe_grass_types,
        "application_timing": p.application_timing,
        "notes": p.notes,
        "is_builtin": p.is_builtin,
        "is_custom": p.is_custom,
    }


@router.get("/categories")
async def get_categories():
    return PRODUCT_CATEGORIES


@router.get("")
async def list_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    q: Optional[str] = Query(None, description="Search by name or brand"),
    db: AsyncSession = Depends(get_db),
):
    query = select(ProductCatalog).order_by(ProductCatalog.brand, ProductCatalog.name)

    if category:
        query = query.where(ProductCatalog.category == category)
    if brand:
        query = query.where(ProductCatalog.brand == brand)
    if q:
        search = f"%{q}%"
        query = query.where(
            or_(
                ProductCatalog.name.ilike(search),
                ProductCatalog.brand.ilike(search),
                ProductCatalog.category.ilike(search),
            )
        )

    result = await db.execute(query)
    return [_prod_dict(p) for p in result.scalars().all()]


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Product not found")
    return _prod_dict(p)


@router.post("")
async def create_product(data: dict, db: AsyncSession = Depends(get_db)):
    if data.get("category") and data["category"] not in PRODUCT_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Valid: {PRODUCT_CATEGORIES}")

    p = ProductCatalog(
        is_builtin=False,
        is_custom=True,
        name=data.get("name", ""),
        brand=data.get("brand"),
        category=data.get("category"),
        npk_ratio=data.get("npk_ratio"),
        active_ingredient=data.get("active_ingredient"),
        application_rate_per_1k=data.get("application_rate_per_1k"),
        coverage_sqft_per_bag=data.get("coverage_sqft_per_bag"),
        bag_size=data.get("bag_size"),
        safe_grass_types=data.get("safe_grass_types"),
        application_timing=data.get("application_timing"),
        notes=data.get("notes"),
    )
    db.add(p)
    await db.flush()
    return _prod_dict(p)


@router.put("/{product_id}")
async def update_product(product_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Product not found")
    if p.is_builtin and not p.is_custom:
        raise HTTPException(403, "Cannot edit built-in products")

    for key in ["name", "brand", "category", "npk_ratio", "active_ingredient",
                "application_rate_per_1k", "coverage_sqft_per_bag", "bag_size",
                "safe_grass_types", "application_timing", "notes"]:
        if key in data:
            setattr(p, key, data[key])
    return _prod_dict(p)


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Product not found")
    if p.is_builtin and not p.is_custom:
        raise HTTPException(403, "Cannot delete built-in products")
    await db.delete(p)
    return {"ok": True}
