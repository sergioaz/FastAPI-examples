from fastapi import Query
from typing import Optional

from fastapi import FastAPI

from pydantic import BaseModel
from fastapi.responses import ORJSONResponse

products = {
    1: {"id": 1, "name": "Laptop", "category": "Electronics", "price": 999.99},
    2: {"id": 2, "name": "Smartphone", "category": "Electronics", "price": 699.99},
    3: {"id": 3, "name": "Coffee Maker", "category": "Home Appliances", "price": 49.99},
    4: {"id": 4, "name": "Blender", "category": "Home Appliances", "price": 29.99},
}

app = FastAPI(default_response_class=ORJSONResponse)
@app.get("/products/search/")
async def search_products(
    q: str = Query(min_length=3),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    results = [
        p for p in products.values()
        if q.lower() in p.name.lower()
        and (category is None or p.category == category)
        and (min_price is None or p.price >= min_price)
        and (max_price is None or p.price <= max_price)
    ]
    return {
        "total": len(results),
        "offset": offset,
        "limit": limit,
        "results": results[offset : offset + limit]
    }